#!/usr/bin/env python
# Copyright (c) Meta Platforms, Inc. and affiliates.

import math
import time
from typing import List

from PIL import Image

from pdqhashing.types.containers import HashAndQuality, HashesAndQuality
from pdqhashing.types.hash256 import Hash256
from pdqhashing.utils.matrix import MatrixUtil


class PDQHasher:
    """The only class state is the DCT matrix, so this class may either be
    instantiated once per image, or instantiated once and used for all images;
    the latter will be slightly faster as the DCT matrix will not need to be
    recomputed once per image. Methods are threadsafe."""

    #  From Wikipedia: standard RGB to luminance (the 'Y' in 'YUV').
    LUMA_FROM_R_COEFF = float(0.299)
    LUMA_FROM_G_COEFF = float(0.587)
    LUMA_FROM_B_COEFF = float(0.114)
    DCT_MATRIX_SCALE_FACTOR = float(math.sqrt(2.0 / 64.0))

    #  Wojciech Jarosz 'Fast Image Convolutions' ACM SIGGRAPH 2001:
    #  X,Y,X,Y passes of 1-D box filters produces a 2D tent filter.
    PDQ_NUM_JAROSZ_XY_PASSES = 2

    #  Since PDQ uses 64x64 blocks, 1/64th of the image height/width
    #  respectively is a full block. But since we use two passes, we want half
    #  that window size per pass. Example: 1024x1024 full-resolution input. PDQ
    #  downsamples to 64x64. Each 16x16 block of the input produces a single
    #  downsample pixel.  X,Y passes with window size 8 (= 1024/128) average
    #  pixels with 8x8 neighbors. The second X,Y pair of 1D box-filter passes
    #  accumulate data from all 16x16.
    PDQ_JAROSZ_WINDOW_SIZE_DIVISOR = 128

    #  Flags for which dihedral-transforms are desired to be produced.
    PDQ_DO_DIH_ORIGINAL = 0x01
    PDQ_DO_DIH_ROTATE_90 = 0x02
    PDQ_DO_DIH_ROTATE_180 = 0x04
    PDQ_DO_DIH_ROTATE_270 = 0x08
    PDQ_DO_DIH_FLIPX = 0x10
    PDQ_DO_DIH_FLIPY = 0x20
    PDQ_DO_DIH_FLIP_PLUS1 = 0x40
    PDQ_DO_DIH_FLIP_MINUS1 = 0x80
    PDQ_DO_DIH_ALL = 0xFF

    DCT_matrix: List[List[float]] = []

    def compute_dct_matrix(self):
        d = [0] * 16
        for i in range(0, 16):
            di = [0] * 64
            for j in range(0, 64):
                di[j] = self.DCT_MATRIX_SCALE_FACTOR * math.cos((math.pi / 2 / 64.0) * (i + 1) * (2 * j + 1))
            d[i] = di
        return d

    def __init__(self) -> None:
        """Christoph Zauner 'Implementation and Benchmarking of Perceptual
        Image Hash Functions' 2010

        See also comments on dct64To16. Input is (0..63)x(0..63); output is
        (1..16)x(1..16) with the latter indexed as (0..15)x(0..15).
        Returns 16x64 matrix."""
        self.DCT_matrix = self.compute_dct_matrix()

    class HashingMetadata:
        def __init__(self) -> None:
            self.readSeconds = float(-1.0)
            self.hashSeconds = float(-1.0)
            self.imageHeightTimesWidth = -1

    def fromFile(self, filepath, hashingMetadata=None):
        t1 = time.time()
        img = None
        try:
            img = Image.open(filepath)
            # resizing the image proportionally to max 512px width and max 512px height
            img.thumbnail((512, 512))
        except IOError as e:
            raise e
        t2 = time.time()
        readSeconds = t2 - t1
        numCols, numRows = img.size
        buffer1 = MatrixUtil.allocateMatrixAsRowMajorArray(numRows, numCols)
        buffer2 = MatrixUtil.allocateMatrixAsRowMajorArray(numRows, numCols)
        buffer64x64 = MatrixUtil.allocateMatrix(64, 64)
        buffer16x64 = MatrixUtil.allocateMatrix(16, 64)
        buffer16x16 = MatrixUtil.allocateMatrix(16, 16)
        t1 = time.time()
        rv = self.fromImage(
            img, buffer1, buffer2, buffer64x64, buffer16x64, buffer16x16
        )
        t2 = time.time()

        if hashingMetadata is not None:
            hashingMetadata.imageHeightTimesWidth = numRows * numCols
            hashingMetadata.readSeconds = readSeconds
            hashingMetadata.hashSeconds = t2 - t1
        return rv

    def fromBufferedImage(self, img_bytes):
        try:
            img = Image.open(img_bytes)
            # resizing the image proportionally to max 512px width and max 512px height
            img.thumbnail((512, 512))
        except IOError as e:
            raise e
        numCols, numRows = img.size
        buffer1 = MatrixUtil.allocateMatrixAsRowMajorArray(numRows, numCols)
        buffer2 = MatrixUtil.allocateMatrixAsRowMajorArray(numRows, numCols)
        buffer64x64 = MatrixUtil.allocateMatrix(64, 64)
        buffer16x64 = MatrixUtil.allocateMatrix(16, 64)
        buffer16x16 = MatrixUtil.allocateMatrix(16, 16)
        return self.fromImage(
            img, buffer1, buffer2, buffer64x64, buffer16x64, buffer16x16
        )

    def fromImage(self, img, buffer1, buffer2, buffer64x64, buffer16x64, buffer16x16):
        numCols, numRows = img.size
        self.fillFloatLumaFromBufferImage(img, buffer1)
        return self.pdqHash256FromFloatLuma(
            buffer1, buffer2, numRows, numCols, buffer64x64, buffer16x64, buffer16x16
        )

    def fillFloatLumaFromBufferImage(self, img, luma):
        numCols, numRows = img.size
        rgb_image = img.convert("RGB")
        pixels = rgb_image.load()

        for i in range(numRows):
            for j in range(numCols):
                r, g, b = pixels[j, i]
                luma[i * numCols + j] = (
                    self.LUMA_FROM_R_COEFF * r
                    + self.LUMA_FROM_G_COEFF * g
                    + self.LUMA_FROM_B_COEFF * b
                )

    def pdqHash256FromFloatLuma(
        self,
        fullBuffer1,
        fullBuffer2,
        numRows,
        numCols,
        buffer64x64,
        buffer16x64,
        buffer16x16,
    ):
        windowSizeAlongRows = self.computeJaroszFilterWindowSize(numCols)
        windowSizeAlongCols = self.computeJaroszFilterWindowSize(numRows)
        self.jaroszFilterFloat(
            fullBuffer1,
            fullBuffer2,
            numRows,
            numCols,
            windowSizeAlongRows,
            windowSizeAlongCols,
            self.PDQ_NUM_JAROSZ_XY_PASSES,
        )
        self.decimateFloat(fullBuffer1, numRows, numCols, buffer64x64)
        quality = self.computePDQImageDomainQualityMetric(buffer64x64)
        self.dct64To16(buffer64x64, buffer16x64, buffer16x16)
        hash = self.pdqBuffer16x16ToBits(buffer16x16)
        return HashAndQuality(hash, quality)

    def dihedralFromFile(self, filename, hashingMetadata, dihFlags):
        t1 = time.time()
        img = None
        try:
            img = Image.open(filename)
        except IOError as e:
            raise e
        t2 = time.time()
        hashingMetadata.readSeconds = t2 - t1
        numCols, numRows = img.size
        hashingMetadata.imageHeightTimesWidth = numRows * numCols
        buffer1 = MatrixUtil.allocateMatrixAsRowMajorArray(numRows, numCols)
        buffer2 = MatrixUtil.allocateMatrixAsRowMajorArray(numRows, numCols)
        buffer64x64 = MatrixUtil.allocateMatrix(64, 64)
        buffer16x64 = MatrixUtil.allocateMatrix(16, 64)
        buffer16x16 = MatrixUtil.allocateMatrix(16, 16)
        buffer16x16Aux = MatrixUtil.allocateMatrix(16, 16)
        t1 = time.time()
        rv = self.dihedralFromBufferedImage(
            img,
            buffer1,
            buffer2,
            buffer64x64,
            buffer16x64,
            buffer16x16,
            buffer16x16Aux,
            dihFlags,
        )
        t2 = time.time()
        hashingMetadata.hashSeconds = t2 - t1
        return rv

    def dihedralFromBufferedImage(
        self,
        img,
        buffer1,
        buffer2,
        buffer64x64,
        buffer16x64,
        buffer16x16,
        buffer16x16Aux,
        dihFlags,
    ):
        numCols, numRows = img.size
        self.fillFloatLumaFromBufferImage(img, buffer1)
        return self.pdqHash256esFromFloatLuma(
            buffer1,
            buffer2,
            numRows,
            numCols,
            buffer64x64,
            buffer16x64,
            buffer16x16,
            buffer16x16Aux,
            dihFlags,
        )

    def pdqHash256esFromFloatLuma(
        self,
        fullBuffer1,
        fullBuffer2,
        numRows,
        numCols,
        buffer64x64,
        buffer16x64,
        buffer16x16,
        buffer16x16Aux,
        dihFlags,
    ):
        windowSizeAlongRows = self.computeJaroszFilterWindowSize(numCols)
        windowSizeAlongCols = self.computeJaroszFilterWindowSize(numRows)
        self.jaroszFilterFloat(
            fullBuffer1,
            fullBuffer2,
            numRows,
            numCols,
            windowSizeAlongRows,
            windowSizeAlongCols,
            self.PDQ_NUM_JAROSZ_XY_PASSES,
        )
        self.decimateFloat(fullBuffer1, numRows, numCols, buffer64x64)
        quality = self.computePDQImageDomainQualityMetric(buffer64x64)
        self.dct64To16(buffer64x64, buffer16x64, buffer16x16)
        hash = None
        hashRotate90 = None
        hashRotate180 = None
        hashRotate270 = None
        hashFlipX = None
        hashFlipY = None
        hashFlipPlus1 = None
        hashFlipMinus1 = None
        if (dihFlags & self.PDQ_DO_DIH_ORIGINAL) != 0:
            hash = self.pdqBuffer16x16ToBits(buffer16x16)
        if (dihFlags & self.PDQ_DO_DIH_ROTATE_90) != 0:
            self.dct16OriginalToRotate90(buffer16x16, buffer16x16Aux)
            hashRotate90 = self.pdqBuffer16x16ToBits(buffer16x16Aux)
        if (dihFlags & self.PDQ_DO_DIH_ROTATE_180) != 0:
            self.dct16OriginalToRotate180(buffer16x16, buffer16x16Aux)
            hashRotate180 = self.pdqBuffer16x16ToBits(buffer16x16Aux)
        if (dihFlags & self.PDQ_DO_DIH_ROTATE_270) != 0:
            self.dct16OriginalToRotate270(buffer16x16, buffer16x16Aux)
            hashRotate270 = self.pdqBuffer16x16ToBits(buffer16x16Aux)
        if (dihFlags & self.PDQ_DO_DIH_FLIPX) != 0:
            self.dct16OriginalToFlipX(buffer16x16, buffer16x16Aux)
            hashFlipX = self.pdqBuffer16x16ToBits(buffer16x16Aux)
        if (dihFlags & self.PDQ_DO_DIH_FLIPY) != 0:
            self.dct16OriginalToFlipY(buffer16x16, buffer16x16Aux)
            hashFlipY = self.pdqBuffer16x16ToBits(buffer16x16Aux)
        if (dihFlags & self.PDQ_DO_DIH_FLIP_PLUS1) != 0:
            self.dct16OriginalToFlipPlus1(buffer16x16, buffer16x16Aux)
            hashFlipPlus1 = self.pdqBuffer16x16ToBits(buffer16x16Aux)
        if (dihFlags & self.PDQ_DO_DIH_FLIP_MINUS1) != 0:
            self.dct16OriginalToFlipMinus1(buffer16x16, buffer16x16Aux)
            hashFlipMinus1 = self.pdqBuffer16x16ToBits(buffer16x16Aux)
        return HashesAndQuality(
            hash,
            hashRotate90,
            hashRotate180,
            hashRotate270,
            hashFlipX,
            hashFlipY,
            hashFlipPlus1,
            hashFlipMinus1,
            quality,
        )

    @classmethod
    def decimateFloat(
        cls, in_, inNumRows, inNumCols, out  # numRows x numCols in row-major order
    ):
        for i in range(64):
            ini = int(((i + 0.5) * inNumRows) / 64)
            for j in range(64):
                inj = int(((j + 0.5) * inNumCols) / 64)
                out[i][j] = in_[ini * inNumCols + inj]

    @classmethod
    def computePDQImageDomainQualityMetric(cls, buffer64x64):
        """This is all heuristic (see the PDQ hashing doc). Quantization
        matters since we want to count *significant* gradients, not just the
        some of many small ones. The constants are all manually selected, and
        tuned as described in the document.
        """
        gradientSum = 0
        for i in range(63):
            for j in range(64):
                u = buffer64x64[i][j]
                v = buffer64x64[i + 1][j]
                d = int(((u - v) * 100) / 255)
                gradientSum += int(abs(d))
        for i in range(64):
            for j in range(63):
                u = buffer64x64[i][j]
                v = buffer64x64[i][j + 1]
                d = int(((u - v) * 100) / 255)
                gradientSum += int(abs(d))
        quality = int(gradientSum / 90)
        if quality > 100:
            quality = 100
        return quality

    def dct64To16(self, A, T, B):
        """Full 64x64 to 64x64 can be optimized e.g. the Lee algorithm.
        But here we only want slots (1-16)x(1-16) of the full 64x64 output.
        Careful experiments showed that using Lee along all 64 slots in one
        dimension, then Lee along 16 slots in the second, followed by
        extracting slots 1-16 of the output, was actually slower than the
        current implementation which is completely non-clever/non-Lee but
        computes only what is needed."""
        D = self.DCT_matrix

        # B = D A Dt
        # B = (D A) Dt ; T = D A
        # T is 16x64;

        # T = D A
        # Tij = sum {k} Dik Akj

        T = [0] * 16
        for i in range(0, 16):
            ti = [0] * 64
            for j in range(0, 64):
                tij = 0.0
                for k in range(0, 64):
                    tij += D[i][k] * A[k][j]
                ti[j] = tij
            T[i] = ti

        # B = T Dt
        # Bij = sum {k} Tik Djk
        for i in range(16):
            for j in range(16):
                sumk = float(0.0)
                for k in range(64):
                    sumk += T[i][k] * D[j][k]
                B[i][j] = sumk

    """
    -------------------------------------
    orig      rot90     rot180    rot270
    noxpose   xpose     noxpose   xpose
    + + + +   - + - +   + - + -   - - - -
    + + + +   - + - +   - + - +   + + + +
    + + + +   - + - +   + - + -   - - - -
    + + + +   - + - +   - + - +   + + + +

    flipx     flipy     flipplus  flipminus
    noxpose   noxpose   xpose     xpose
    - - - -   - + - +   + + + +   + - + -
    + + + +   - + - +   + + + +   - + - +
    - - - -   - + - +   + + + +   + - + -
    + + + +   - + - +   + + + +   - + - +
    -------------------------------------
    """

    def dct16OriginalToRotate90(self, A, B):
        for i in range(16):
            for j in range(16):
                if (j & 1) != 0:
                    B[j][i] = A[i][j]
                else:
                    B[j][i] = -A[i][j]

    def dct16OriginalToRotate180(self, A, B):
        for i in range(16):
            for j in range(16):
                if ((i + j) & 1) != 0:
                    B[i][j] = -A[i][j]
                else:
                    B[i][j] = A[i][j]

    def dct16OriginalToRotate270(self, A, B):
        for i in range(16):
            for j in range(16):
                if (i & 1) != 0:
                    B[j][i] = A[i][j]
                else:
                    B[j][i] = -A[i][j]

    def dct16OriginalToFlipX(self, A, B):
        i = 0
        for i in range(16):
            for j in range(16):
                if (i & 1) != 0:
                    B[i][j] = A[i][j]
                else:
                    B[i][j] = -A[i][j]

    def dct16OriginalToFlipY(self, A, B):
        for i in range(16):
            for j in range(16):
                if (j & 1) != 0:
                    B[i][j] = A[i][j]
                else:
                    B[i][j] = -A[i][j]

    def dct16OriginalToFlipPlus1(self, A, B):
        for i in range(16):
            for j in range(16):
                B[j][i] = A[i][j]

    def dct16OriginalToFlipMinus1(self, A, B):
        for i in range(16):
            for j in range(16):
                if ((i + j) & 1) != 0:
                    B[j][i] = -A[i][j]
                else:
                    B[j][i] = A[i][j]

    def pdqBuffer16x16ToBits(self, dctOutput16x16):
        """
        Each bit of the 16x16 output hash is for whether the given frequency
        component is greater than the median frequency component or not.
        """
        hash = Hash256()
        dctMedian = MatrixUtil.torben(dctOutput16x16, 16, 16)
        for i in range(16):
            for j in range(16):
                if dctOutput16x16[i][j] > dctMedian:
                    hash.setBit(i * 16 + j)
        return hash

    @classmethod
    def computeJaroszFilterWindowSize(cls, dimension):
        """Round up. See comments at top of file for details."""
        return int(
            (dimension + cls.PDQ_JAROSZ_WINDOW_SIZE_DIVISOR - 1)
            / cls.PDQ_JAROSZ_WINDOW_SIZE_DIVISOR
        )

    @classmethod
    def jaroszFilterFloat(
        cls,
        buffer1,
        buffer2,
        numRows,
        numCols,
        windowSizeAlongRows,
        windowSizeAlongCols,
        nreps,
    ):
        for _i in range(nreps):
            cls.boxAlongRowsFloat(
                buffer1, buffer2, numRows, numCols, windowSizeAlongRows
            )
            cls.boxAlongColsFloat(
                buffer2, buffer1, numRows, numCols, windowSizeAlongCols
            )

    """
    ----------------------------------------------------------------
    # 7 and 4
    #
    #    0 0 0 0 0 0 0 0 0 0 1 1 1 1 1 1
    #    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5
    #
    #    .                                PHASE 1: ONLY ADD, NO WRITE, NO SUBTRACT
    #    . .
    #    . . .
    #
    #  0 * . . .                          PHASE 2: ADD, WRITE, WITH NO SUBTRACTS
    #  1 . * . . .
    #  2 . . * . . .
    #  3 . . . * . . .
    #
    #  4   . . . * . . .                  PHASE 3: WRITES WITH ADD & SUBTRACT
    #  5     . . . * . . .
    #  6       . . . * . . .
    #  7         . . . * . . .
    #  8           . . . * . . .
    #  9             . . . * . . .
    # 10               . . . * . . .
    # 11                 . . . * . . .
    # 12                   . . . * . . .
    #
    # 13                     . . . * . .  PHASE 4: FINAL WRITES WITH NO ADDS
    # 14                       . . . * .
    # 15                         . . . *
    #
    #         = 0                                     =  0   PHASE 1
    #         = 0+1                                   =  1
    #         = 0+1+2                                 =  3
    #
    # out[ 0] = 0+1+2+3                               =  6   PHASE 2
    # out[ 1] = 0+1+2+3+4                             = 10
    # out[ 2] = 0+1+2+3+4+5                           = 15
    # out[ 3] = 0+1+2+3+4+5+6                         = 21
    #
    # out[ 4] =   1+2+3+4+5+6+7                       = 28   PHASE 3
    # out[ 5] =     2+3+4+5+6+7+8                     = 35
    # out[ 6] =       3+4+5+6+7+8+9                   = 42
    # out[ 7] =         4+5+6+7+8+9+10                = 49
    # out[ 8] =           5+6+7+8+9+10+11             = 56
    # out[ 9] =             6+7+8+9+10+11+12          = 63
    # out[10] =               7+8+9+10+11+12+13       = 70
    # out[11] =                 8+9+10+11+12+13+14    = 77
    # out[12] =                   9+10+11+12+13+14+15 = 84
    #
    # out[13] =                     10+11+12+13+14+15 = 75  PHASE 4
    # out[14] =                        11+12+13+14+15 = 65
    # out[15] =                           12+13+14+15 = 54
    # ----------------------------------------------------------------

    # ----------------------------------------------------------------
    # 8 and 5
    #
    #    0 0 0 0 0 0 0 0 0 0 1 1 1 1 1 1
    #    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5
    #
    #    .                                PHASE 1: ONLY ADD, NO WRITE, NO SUBTRACT
    #    . .
    #    . . .
    #    . . . .
    #
    #  0 * . . . .                        PHASE 2: ADD, WRITE, WITH NO SUBTRACTS
    #  1 . * . . . .
    #  2 . . * . . . .
    #  3 . . . * . . . .
    #
    #  4   . . . * . . . .                PHASE 3: WRITES WITH ADD & SUBTRACT
    #  5     . . . * . . . .
    #  6       . . . * . . . .
    #  7         . . . * . . . .
    #  8           . . . * . . . .
    #  9             . . . * . . . .
    # 10               . . . * . . . .
    # 11                 . . . * . . . .
    #
    # 12                   . . . * . . .  PHASE 4: FINAL WRITES WITH NO ADDS
    # 13                     . . . * . .
    # 14                       . . . * .
    # 15                         . . . *
    #
    #         = 0                                     =  0   PHASE 1
    #         = 0+1                                   =  1
    #         = 0+1+2                                 =  3
    #         = 0+1+2+3                               =  6
    #
    # out[ 0] = 0+1+2+3+4                             = 10
    # out[ 1] = 0+1+2+3+4+5                           = 15
    # out[ 2] = 0+1+2+3+4+5+6                         = 21
    # out[ 3] = 0+1+2+3+4+5+6+7                       = 28
    #
    # out[ 4] =   1+2+3+4+5+6+7+8                     = 36   PHASE 3
    # out[ 5] =     2+3+4+5+6+7+8+9                   = 44
    # out[ 6] =       3+4+5+6+7+8+9+10                = 52
    # out[ 7] =         4+5+6+7+8+9+10+11             = 60
    # out[ 8] =           5+6+7+8+9+10+11+12          = 68
    # out[ 9] =             6+7+8+9+10+11+12+13       = 76
    # out[10] =               7+8+9+10+11+12+13+14    = 84
    # out[11] =                 8+9+10+11+12+13+14+15 = 92
    #
    # out[12] =                   9+10+11+12+13+14+15 = 84  PHASE 4
    # out[13] =                     10+11+12+13+14+15 = 75  PHASE 4
    # out[14] =                        11+12+13+14+15 = 65
    # out[15] =                           12+13+14+15 = 54
    ----------------------------------------------------------------
    """

    @classmethod
    def box1DFloat(
        cls,
        invec,
        inStartOffset,
        outvec,
        outStartOffset,
        vectorLength,
        stride,
        fullWindowSize,
    ):

        halfWindowSize = int((fullWindowSize + 2) / 2)  # 7->4, 8->5
        phase_1_nreps = int(halfWindowSize - 1)
        phase_2_nreps = int(fullWindowSize - halfWindowSize + 1)
        phase_3_nreps = int(vectorLength - fullWindowSize)
        phase_4_nreps = int(halfWindowSize - 1)
        li = 0  # Index of left edge of read window, for subtracts
        ri = 0  # Index of right edge of read windows, for adds
        oi = 0  # Index into output vector
        sum = float(0.0)
        currentWindowSize = 0

        # PHASE 1: ACCUMULATE FIRST SUM NO WRITES
        i = 0
        while i < phase_1_nreps:
            sum += invec[inStartOffset + ri]
            currentWindowSize += 1
            ri += stride
            i += 1
        # PHASE 2: INITIAL WRITES WITH SMALL WINDOW
        i = 0
        while i < phase_2_nreps:
            sum += invec[inStartOffset + ri]
            currentWindowSize += 1
            outvec[outStartOffset + oi] = sum / currentWindowSize
            ri += stride
            oi += stride
            i += 1
        # PHASE 3: WRITES WITH FULL WINDOW
        i = 0
        while i < phase_3_nreps:
            sum += invec[inStartOffset + ri]
            sum -= invec[inStartOffset + li]
            outvec[outStartOffset + oi] = sum / currentWindowSize
            li += stride
            ri += stride
            oi += stride
            i += 1
        # PHASE 4: FINAL WRITES WITH SMALL WINDOW
        i = 0
        while i < phase_4_nreps:
            sum -= invec[inStartOffset + li]
            currentWindowSize -= 1
            outvec[outStartOffset + oi] = sum / currentWindowSize
            li += stride
            oi += stride
            i += 1

    @classmethod
    def boxAlongRowsFloat(cls, input, output, numRows, numCols, windowSize):
        """
        input - matrix as numRows x numCols in row-major order
        output - matrix as numRows x numCols in row-major order
        """
        i = 0
        while i < numRows:
            cls.box1DFloat(
                input,
                i * numCols,
                output,
                i * numCols,
                numCols,
                1,  # stride
                windowSize,
            )
            i += 1

    @classmethod
    def boxAlongColsFloat(cls, input, output, numRows, numCols, windowSize):
        """
        input - matrix as numRows x numCols in row-major order
        out - matrix as numRows x numCols in row-major order
        """
        j = 0
        while j < numCols:
            cls.box1DFloat(input, j, output, j, numRows, numCols, windowSize)
            j += 1
