// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

package pdqhashing.hasher;

import pdqhashing.types.Hash256;
import pdqhashing.types.HashAndQuality;
import pdqhashing.types.HashesAndQuality;
import pdqhashing.utils.MatrixUtil;

import java.lang.Math;
import java.io.File;
import java.io.IOException;
import java.awt.image.BufferedImage;
import javax.imageio.ImageIO;

/**
 * The only class state is the DCT matrix, so this class may either be instantiated once per
 * image, or instantiated once and used for all images; the latter will be slightly faster
 * as the DCT matrix will not need to be recomputed once per image. Methods are threadsafe.
 */
public class PDQHasher {

  // ----------------------------------------------------------------
  // From Wikipedia: standard RGB to luminance (the 'Y' in 'YUV').
  private static final float LUMA_FROM_R_COEFF = (float)0.299;
  private static final float LUMA_FROM_G_COEFF = (float)0.587;
  private static final float LUMA_FROM_B_COEFF = (float)0.114;

  private static final float DCT_MATRIX_SCALE_FACTOR = (float)Math.sqrt(2.0 / 64.0);

  // ----------------------------------------------------------------
  // Wojciech Jarosz 'Fast Image Convolutions' ACM SIGGRAPH 2001:
  // X,Y,X,Y passes of 1-D box filters produces a 2D tent filter.
  public static final int PDQ_NUM_JAROSZ_XY_PASSES = 2;

  // Since PDQ uses 64x64 blocks, 1/64th of the image height/width respectively is
  // a full block. But since we use two passes, we want half that window size per
  // pass. Example: 1024x1024 full-resolution input. PDQ downsamples to 64x64.
  // Each 16x16 block of the input produces a single downsample pixel.  X,Y passes
  // with window size 8 (= 1024/128) average pixels with 8x8 neighbors. The second
  // X,Y pair of 1D box-filter passes accumulate data from all 16x16.
  public static final int PDQ_JAROSZ_WINDOW_SIZE_DIVISOR = 128;

  // ----------------------------------------------------------------
  // Flags for which dihedral-transforms are desired to be produced.
  public static final int PDQ_DO_DIH_ORIGINAL = 0x01;
  public static final int PDQ_DO_DIH_ROTATE_90 = 0x02;
  public static final int PDQ_DO_DIH_ROTATE_180 = 0x04;
  public static final int PDQ_DO_DIH_ROTATE_270 = 0x08;
  public static final int PDQ_DO_DIH_FLIPX = 0x10;
  public static final int PDQ_DO_DIH_FLIPY = 0x20;
  public static final int PDQ_DO_DIH_FLIP_PLUS1 = 0x40;
  public static final int PDQ_DO_DIH_FLIP_MINUS1 = 0x80;
  public static final int PDQ_DO_DIH_ALL = 0xff;

  // ================================================================
  private final float[][] DCT_matrix;
  public PDQHasher() {

    // Christoph Zauner 'Implementation and Benchmarking of Perceptual
    // Image Hash Functions' 2010
    //
    // See also comments on dct64To16. Input is (0..63)x(0..63); output is
    // (1..16)x(1..16) with the latter indexed as (0..15)x(0..15).
    // Returns 16x64 matrix.
    this.DCT_matrix = MatrixUtil.allocateMatrix(16, 64);
    for (int i = 0; i < 16; i++) {
      for (int j = 0; j < 64; j++) {
        this.DCT_matrix[i][j] = (float)(DCT_MATRIX_SCALE_FACTOR *
          Math.cos((Math.PI / 2 / 64.0) * (i+1) * (2 * j + 1)));
      }
    }
  }

  // ================================================================
  // Supporting info returned by the hashing operation
  public static class HashingMetadata {
    public float readSeconds;
    public float hashSeconds;
    public int imageHeightTimesWidth;
    public HashingMetadata() {
      this.readSeconds = (float)-1.0;
      this.hashSeconds = (float)-1.0;
      this.imageHeightTimesWidth = -1;
    }
  }

  // ----------------------------------------------------------------
  public HashAndQuality fromFile(
    String filename,
    HashingMetadata hashingMetadata)
      throws IOException
  {
    long t1, t2;

    t1 = System.nanoTime();
    BufferedImage img = null;
    try {
      img = ImageIO.read(new File(filename));
    } catch (IOException e) {
      throw e;
    }
    t2 = System.nanoTime();
    hashingMetadata.readSeconds = (float)((t2 - t1) / 1e9);

    int numRows = img.getHeight();
    int numCols = img.getWidth();
    hashingMetadata.imageHeightTimesWidth = numRows * numCols;

    float[] buffer1 = MatrixUtil.allocateMatrixAsRowMajorArray(numRows, numCols);
    float[] buffer2 = MatrixUtil.allocateMatrixAsRowMajorArray(numRows, numCols);
    float[][] buffer64x64 = MatrixUtil.allocateMatrix(64, 64);
    float[][] buffer16x64 = MatrixUtil.allocateMatrix(16, 64);
    float[][] buffer16x16 = MatrixUtil.allocateMatrix(16, 16);

    t1 = System.nanoTime();
    HashAndQuality rv = fromBufferedImage(img, buffer1, buffer2, buffer64x64, buffer16x64, buffer16x16);
    t2 = System.nanoTime();
    hashingMetadata.hashSeconds = (float)((t2 - t1) / 1e9);

    return rv;
  }

  // ----------------------------------------------------------------
  // The buffers could be allocated within this method rather than being passed in.
  // This is coded with an eye to the future wherein we could hash video frames,
  // all of which would be the same dimension, and the buffers could be reused.
  public HashAndQuality fromBufferedImage(
    BufferedImage img,
    float[] buffer1, // image numRows x numCols as row-major array
    float[] buffer2, // image numRows x numCols as row-major array
    float[][] buffer64x64,
    float[][] buffer16x64,
    float[][] buffer16x16)
  {
    int numRows = img.getHeight();
    int numCols = img.getWidth();

    fillFloatLumaFromBufferImage(img, buffer1);

    return pdqHash256FromFloatLuma(buffer1, buffer2, numRows, numCols,
      buffer64x64, buffer16x64, buffer16x16);
  }

  // ----------------------------------------------------------------
  // Made public for test/demo access
  public void fillFloatLumaFromBufferImage(
    BufferedImage img,
    float[] luma) // image numRows x numCols as row-major array
  {
    int numRows = img.getHeight();
    int numCols = img.getWidth();

    for (int i = 0; i < numRows; i++) {
      for (int j = 0; j < numCols; j++) {
        int rgb = img.getRGB(j, i); // xxx check semantics of these packed-as-int pixels
        int r = (rgb >> 16) & 0xff;
        int g = (rgb >> 8) & 0xff;
        int b = rgb & 0xff;
        luma[i * numCols + j] =
          LUMA_FROM_R_COEFF * r +
          LUMA_FROM_G_COEFF * g +
          LUMA_FROM_B_COEFF * b;
      }
    }
  }

  // ----------------------------------------------------------------
  public HashAndQuality pdqHash256FromFloatLuma(
    float[] fullBuffer1, // image numRows x numCols as row-major array
    float[] fullBuffer2, // image numRows x numCols as row-major array
    int numRows,
    int numCols,
    float[][] buffer64x64,
    float[][] buffer16x64,
    float[][] buffer16x16)
  {
    // Downsample (blur and decimate)
    int windowSizeAlongRows = computeJaroszFilterWindowSize(numCols);
    int windowSizeAlongCols = computeJaroszFilterWindowSize(numRows);

    jaroszFilterFloat(
      fullBuffer1,
      fullBuffer2,
      numRows,
      numCols,
      windowSizeAlongRows,
      windowSizeAlongCols,
      PDQ_NUM_JAROSZ_XY_PASSES
    );

    decimateFloat(fullBuffer1, numRows, numCols, buffer64x64);

    // Quality metric.  Reuse the 64x64 image-domain downsample
    // since we already have it.
    int quality = computePDQImageDomainQualityMetric(buffer64x64);

    // 2D DCT
    dct64To16(buffer64x64, buffer16x64, buffer16x16);

    //  Output bits
    Hash256 hash = pdqBuffer16x16ToBits(buffer16x16);

    return new HashAndQuality(hash, quality);
  }

  // ----------------------------------------------------------------
  public HashesAndQuality dihedralFromFile(
    String filename,
    HashingMetadata hashingMetadata,
    int dihFlags) // PDQ_DO_DIH_ORIGINAL et al.
      throws IOException
  {
    long t1, t2;

    t1 = System.nanoTime();
    BufferedImage img = null;
    try {
      img = ImageIO.read(new File(filename));
    } catch (IOException e) {
      throw e;
    }
    t2 = System.nanoTime();
    hashingMetadata.readSeconds = (float)((t2 - t1) / 1e9);

    int numRows = img.getHeight();
    int numCols = img.getWidth();
    hashingMetadata.imageHeightTimesWidth = numRows * numCols;

    float[] buffer1 = MatrixUtil.allocateMatrixAsRowMajorArray(numRows, numCols);
    float[] buffer2 = MatrixUtil.allocateMatrixAsRowMajorArray(numRows, numCols);
    float[][] buffer64x64 = MatrixUtil.allocateMatrix(64, 64);
    float[][] buffer16x64 = MatrixUtil.allocateMatrix(16, 64);
    float[][] buffer16x16 = MatrixUtil.allocateMatrix(16, 16);
    float[][] buffer16x16Aux = MatrixUtil.allocateMatrix(16, 16);

    t1 = System.nanoTime();
    HashesAndQuality rv = dihedralFromBufferedImage(img, buffer1, buffer2, buffer64x64, buffer16x64,
      buffer16x16, buffer16x16Aux, dihFlags);
    t2 = System.nanoTime();
    hashingMetadata.hashSeconds = (float)((t2 - t1) / 1e9);

    return rv;
  }

  // ----------------------------------------------------------------
  // The buffers could be allocated within this method rather than being passed in.
  // This is coded with an eye to the future wherein we could hash video frames,
  // all of which would be the same dimension, and the buffers could be reused.
  public HashesAndQuality dihedralFromBufferedImage(
    BufferedImage img,
    float[] buffer1, // image numRows x numCols as row-major array
    float[] buffer2, // image numRows x numCols as row-major array
    float[][] buffer64x64,
    float[][] buffer16x64,
    float[][] buffer16x16,
    float[][] buffer16x16Aux,
    int dihFlags)
  {
    int numRows = img.getHeight();
    int numCols = img.getWidth();

    fillFloatLumaFromBufferImage(img, buffer1);

    return pdqHash256esFromFloatLuma(buffer1, buffer2, numRows, numCols,
      buffer64x64, buffer16x64, buffer16x16, buffer16x16Aux, dihFlags);
  }

  // ----------------------------------------------------------------
  public HashesAndQuality pdqHash256esFromFloatLuma(
    float[] fullBuffer1, // image numRows x numCols as row-major array
    float[] fullBuffer2, // image numRows x numCols as row-major array
    int numRows,
    int numCols,
    float[][] buffer64x64,
    float[][] buffer16x64,
    float[][] buffer16x16,
    float[][] buffer16x16Aux,
    int dihFlags)
  {
    // Downsample (blur and decimate)
    int windowSizeAlongRows = computeJaroszFilterWindowSize(numCols);
    int windowSizeAlongCols = computeJaroszFilterWindowSize(numRows);

    jaroszFilterFloat(
      fullBuffer1,
      fullBuffer2,
      numRows,
      numCols,
      windowSizeAlongRows,
      windowSizeAlongCols,
      PDQ_NUM_JAROSZ_XY_PASSES
    );

    decimateFloat(fullBuffer1, numRows, numCols, buffer64x64);

    // Quality metric.  Reuse the 64x64 image-domain downsample
    // since we already have it.
    int quality = computePDQImageDomainQualityMetric(buffer64x64);

    // 2D DCT
    dct64To16(buffer64x64, buffer16x64, buffer16x16);

    //  Output bits
    Hash256 hash = null;
    Hash256 hashRotate90 = null;
    Hash256 hashRotate180 = null;
    Hash256 hashRotate270 = null;
    Hash256 hashFlipX = null;
    Hash256 hashFlipY = null;
    Hash256 hashFlipPlus1 = null;
    Hash256 hashFlipMinus1 = null;

    if ((dihFlags & PDQ_DO_DIH_ORIGINAL) != 0) {
      hash = pdqBuffer16x16ToBits(buffer16x16);
    }
    if ((dihFlags & PDQ_DO_DIH_ROTATE_90) != 0) {
      dct16OriginalToRotate90(buffer16x16, buffer16x16Aux);
      hashRotate90 = pdqBuffer16x16ToBits(buffer16x16Aux);
    }
    if ((dihFlags & PDQ_DO_DIH_ROTATE_180) != 0) {
      dct16OriginalToRotate180(buffer16x16, buffer16x16Aux);
      hashRotate180 = pdqBuffer16x16ToBits(buffer16x16Aux);
    }
    if ((dihFlags & PDQ_DO_DIH_ROTATE_270) != 0) {
      dct16OriginalToRotate270(buffer16x16, buffer16x16Aux);
      hashRotate270 = pdqBuffer16x16ToBits(buffer16x16Aux);
    }
    if ((dihFlags & PDQ_DO_DIH_FLIPX) != 0) {
      dct16OriginalToFlipX(buffer16x16, buffer16x16Aux);
      hashFlipX = pdqBuffer16x16ToBits(buffer16x16Aux);
    }
    if ((dihFlags & PDQ_DO_DIH_FLIPY) != 0) {
      dct16OriginalToFlipY(buffer16x16, buffer16x16Aux);
      hashFlipY = pdqBuffer16x16ToBits(buffer16x16Aux);
    }
    if ((dihFlags & PDQ_DO_DIH_FLIP_PLUS1) != 0) {
      dct16OriginalToFlipPlus1(buffer16x16, buffer16x16Aux);
      hashFlipPlus1 = pdqBuffer16x16ToBits(buffer16x16Aux);
    }
    if ((dihFlags & PDQ_DO_DIH_FLIP_MINUS1) != 0) {
      dct16OriginalToFlipMinus1(buffer16x16, buffer16x16Aux);
      hashFlipMinus1 = pdqBuffer16x16ToBits(buffer16x16Aux);
    }

    return new HashesAndQuality(
      hash,
      hashRotate90,
      hashRotate180,
      hashRotate270,
      hashFlipX,
      hashFlipY,
      hashFlipPlus1,
      hashFlipMinus1,
      quality
    );
  }

  // ----------------------------------------------------------------
  public static void decimateFloat(
    float[] in, // numRows x numCols in row-major order
    int inNumRows,
    int inNumCols,
    float[][] out) // 64x64
  {
    // target centers not corners:
    for (int i = 0; i < 64; i++) {
      int ini = (int)(((i + 0.5) * inNumRows) / 64);
      for (int j = 0; j < 64; j++) {
        int inj = (int)(((j + 0.5) * inNumCols) / 64);
        out[i][j] = in[ini * inNumCols + inj];
      }
    }
  }

  // ----------------------------------------------------------------
  // This is all heuristic (see the PDQ hashing doc). Quantization matters since
  // we want to count *significant* gradients, not just the some of many small
  // ones. The constants are all manually selected, and tuned as described in the
  // document.
  private static int computePDQImageDomainQualityMetric(float[][] buffer64x64) {
    int gradientSum = 0;

    for (int i = 0; i < 63; i++) {
      for (int j = 0; j < 64; j++) {
        float u = buffer64x64[i][j];
        float v = buffer64x64[i+1][j];
        int d = (int)(((u - v) * 100) / 255);
        gradientSum += (int)Math.abs(d);
      }
    }
    for (int i = 0; i < 64; i++) {
      for (int j = 0; j < 63; j++) {
        float u = buffer64x64[i][j];
        float v = buffer64x64[i][j+1];
        int d = (int)(((u - v) * 100) / 255);
        gradientSum += (int)Math.abs(d);
      }
    }

    // Heuristic scaling factor.
    int quality = gradientSum / 90;
    if (quality > 100)
      quality = 100;

    return quality;
    }

  // ----------------------------------------------------------------
  // Full 64x64 to 64x64 can be optimized e.g. the Lee algorithm.  But here we
  // only want slots (1-16)x(1-16) of the full 64x64 output. Careful experiments
  // showed that using Lee along all 64 slots in one dimension, then Lee along 16
  // slots in the second, followed by extracting slots 1-16 of the output, was
  // actually slower than the current implementation which is completely
  // non-clever/non-Lee but computes only what is needed.

  void dct64To16(
    float[][] A, // input: 64x64
    float[][] T, // temp buffer: 16x64
    float[][] B) // output: 16x16
  {
    float[][] D = this.DCT_matrix;

    // B = D A Dt
    // B = (D A) Dt ; T = D A
    // T is 16x64;

    // T = D A
    // Tij = sum {k} Dik Akj
    for (int i = 0; i < 16; i++) {
      for (int j = 0; j < 64; j++) {
        float sumk = (float)0.0;
        for (int k = 0; k < 64; k++) {
          sumk += D[i][k] * A[k][j];
        }
        T[i][j] = sumk;
      }
    }

    // B = T Dt
    // Bij = sum {k} Tik Djk
    for (int i = 0; i < 16; i++) {
      for (int j = 0; j < 16; j++) {
        float sumk = (float)0.0;
        for (int k = 0; k < 64; k++) {
          sumk += T[i][k] * D[j][k];
        }
        B[i][j] = sumk;
      }
    }
  }

  // ----------------------------------------------------------------
  // orig      rot90     rot180    rot270
  // noxpose   xpose     noxpose   xpose
  // + + + +   - + - +   + - + -   - - - -
  // + + + +   - + - +   - + - +   + + + +
  // + + + +   - + - +   + - + -   - - - -
  // + + + +   - + - +   - + - +   + + + +
  //
  // flipx     flipy     flipplus  flipminus
  // noxpose   noxpose   xpose     xpose
  // - - - -   - + - +   + + + +   + - + -
  // + + + +   - + - +   + + + +   - + - +
  // - - - -   - + - +   + + + +   + - + -
  // + + + +   - + - +   + + + +   - + - +

  // ----------------------------------------------------------------
  void dct16OriginalToRotate90(
    float[][] A, // input 16x16
    float[][] B) // output 16x16
  {
    for (int i = 0; i < 16; i++) {
      for (int j = 0; j < 16; j++) {
        if ((j & 1) != 0) {
          B[j][i] = A[i][j];
        } else {
          B[j][i] = -A[i][j];
        }
      }
    }
  }

  void dct16OriginalToRotate180(
    float[][] A, // input 16x16
    float[][] B) // output 16x16
  {
    for (int i = 0; i < 16; i++) {
      for (int j = 0; j < 16; j++) {
        if (((i+j) & 1) != 0) {
          B[i][j] = -A[i][j];
        } else {
          B[i][j] = A[i][j];
        }
      }
    }
  }

  void dct16OriginalToRotate270(
    float[][] A, // input 16x16
    float[][] B) // output 16x16
  {
    for (int i = 0; i < 16; i++) {
      for (int j = 0; j < 16; j++) {
        if ((i & 1) != 0) {
          B[j][i] = A[i][j];
        } else {
          B[j][i] = -A[i][j];
        }
      }
    }
  }

  void dct16OriginalToFlipX(
    float[][] A, // input 16x16
    float[][] B) // output 16x16
  {
    for (int i = 0; i < 16; i++) {
      for (int j = 0; j < 16; j++) {
        if ((i & 1) != 0) {
          B[i][j] = A[i][j];
        } else {
          B[i][j] = -A[i][j];
        }
      }
    }
  }

  void dct16OriginalToFlipY(
    float[][] A, // input 16x16
    float[][] B) // output 16x16
  {
    for (int i = 0; i < 16; i++) {
      for (int j = 0; j < 16; j++) {
        if ((j & 1) != 0) {
          B[i][j] = A[i][j];
        } else {
          B[i][j] = -A[i][j];
        }
      }
    }
  }

  void dct16OriginalToFlipPlus1(
    float[][] A, // input
    float[][] B) // output
  {
    for (int i = 0; i < 16; i++) {
      for (int j = 0; j < 16; j++) {
        B[j][i] = A[i][j];
      }
    }
  }

  void dct16OriginalToFlipMinus1(
    float[][] A, // input 16x16
    float[][] B) // output 16x16
  {
    for (int i = 0; i < 16; i++) {
      for (int j = 0; j < 16; j++) {
        if (((i+j) & 1) != 0) {
          B[j][i] = -A[i][j];
        } else {
          B[j][i] = A[i][j];
        }
      }
    }
  }

  // ----------------------------------------------------------------
  // Each bit of the 16x16 output hash is for whether the given frequency
  // component is greater than the median frequency component or not.
  Hash256 pdqBuffer16x16ToBits(
    float[][] dctOutput16x16
  ) {

    Hash256 hash = new Hash256(); // zero-filled by the constructor

    float dctMedian = MatrixUtil.torben(dctOutput16x16, 16, 16);
    for (int i = 0; i < 16; i++) {
      for (int j = 0; j < 16; j++) {
        if (dctOutput16x16[i][j] > dctMedian) {
          hash.setBit(i*16 + j);
        }
      }
    }

    return hash;
  }

  // ================================================================
  // Round up. See comments at top of file for details.
  public static int computeJaroszFilterWindowSize(int dimension) {
    return (dimension + PDQ_JAROSZ_WINDOW_SIZE_DIVISOR - 1)
      / PDQ_JAROSZ_WINDOW_SIZE_DIVISOR;
  }

  // ----------------------------------------------------------------
  public static void jaroszFilterFloat(
    float[] buffer1, // matrix as numRows x numCols in row-major order
    float[] buffer2, // matrix as numRows x numCols in row-major order
    int numRows,
    int numCols,
    int windowSizeAlongRows,
    int windowSizeAlongCols,
    int nreps)
  {
    for (int i = 0; i < nreps; i++) {
      boxAlongRowsFloat(buffer1, buffer2, numRows, numCols, windowSizeAlongRows);
      boxAlongColsFloat(buffer2, buffer1, numRows, numCols, windowSizeAlongCols);
    }
  }

  // ----------------------------------------------------------------
  // 7 and 4
  //
  //    0 0 0 0 0 0 0 0 0 0 1 1 1 1 1 1
  //    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5
  //
  //    .                                PHASE 1: ONLY ADD, NO WRITE, NO SUBTRACT
  //    . .
  //    . . .
  //
  //  0 * . . .                          PHASE 2: ADD, WRITE, WITH NO SUBTRACTS
  //  1 . * . . .
  //  2 . . * . . .
  //  3 . . . * . . .
  //
  //  4   . . . * . . .                  PHASE 3: WRITES WITH ADD & SUBTRACT
  //  5     . . . * . . .
  //  6       . . . * . . .
  //  7         . . . * . . .
  //  8           . . . * . . .
  //  9             . . . * . . .
  // 10               . . . * . . .
  // 11                 . . . * . . .
  // 12                   . . . * . . .
  //
  // 13                     . . . * . .  PHASE 4: FINAL WRITES WITH NO ADDS
  // 14                       . . . * .
  // 15                         . . . *
  //
  //         = 0                                     =  0   PHASE 1
  //         = 0+1                                   =  1
  //         = 0+1+2                                 =  3
  //
  // out[ 0] = 0+1+2+3                               =  6   PHASE 2
  // out[ 1] = 0+1+2+3+4                             = 10
  // out[ 2] = 0+1+2+3+4+5                           = 15
  // out[ 3] = 0+1+2+3+4+5+6                         = 21
  //
  // out[ 4] =   1+2+3+4+5+6+7                       = 28   PHASE 3
  // out[ 5] =     2+3+4+5+6+7+8                     = 35
  // out[ 6] =       3+4+5+6+7+8+9                   = 42
  // out[ 7] =         4+5+6+7+8+9+10                = 49
  // out[ 8] =           5+6+7+8+9+10+11             = 56
  // out[ 9] =             6+7+8+9+10+11+12          = 63
  // out[10] =               7+8+9+10+11+12+13       = 70
  // out[11] =                 8+9+10+11+12+13+14    = 77
  // out[12] =                   9+10+11+12+13+14+15 = 84
  //
  // out[13] =                     10+11+12+13+14+15 = 75  PHASE 4
  // out[14] =                        11+12+13+14+15 = 65
  // out[15] =                           12+13+14+15 = 54
  // ----------------------------------------------------------------

  // ----------------------------------------------------------------
  // 8 and 5
  //
  //    0 0 0 0 0 0 0 0 0 0 1 1 1 1 1 1
  //    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5
  //
  //    .                                PHASE 1: ONLY ADD, NO WRITE, NO SUBTRACT
  //    . .
  //    . . .
  //    . . . .
  //
  //  0 * . . . .                        PHASE 2: ADD, WRITE, WITH NO SUBTRACTS
  //  1 . * . . . .
  //  2 . . * . . . .
  //  3 . . . * . . . .
  //
  //  4   . . . * . . . .                PHASE 3: WRITES WITH ADD & SUBTRACT
  //  5     . . . * . . . .
  //  6       . . . * . . . .
  //  7         . . . * . . . .
  //  8           . . . * . . . .
  //  9             . . . * . . . .
  // 10               . . . * . . . .
  // 11                 . . . * . . . .
  //
  // 12                   . . . * . . .  PHASE 4: FINAL WRITES WITH NO ADDS
  // 13                     . . . * . .
  // 14                       . . . * .
  // 15                         . . . *
  //
  //         = 0                                     =  0   PHASE 1
  //         = 0+1                                   =  1
  //         = 0+1+2                                 =  3
  //         = 0+1+2+3                               =  6
  //
  // out[ 0] = 0+1+2+3+4                             = 10
  // out[ 1] = 0+1+2+3+4+5                           = 15
  // out[ 2] = 0+1+2+3+4+5+6                         = 21
  // out[ 3] = 0+1+2+3+4+5+6+7                       = 28
  //
  // out[ 4] =   1+2+3+4+5+6+7+8                     = 36   PHASE 3
  // out[ 5] =     2+3+4+5+6+7+8+9                   = 44
  // out[ 6] =       3+4+5+6+7+8+9+10                = 52
  // out[ 7] =         4+5+6+7+8+9+10+11             = 60
  // out[ 8] =           5+6+7+8+9+10+11+12          = 68
  // out[ 9] =             6+7+8+9+10+11+12+13       = 76
  // out[10] =               7+8+9+10+11+12+13+14    = 84
  // out[11] =                 8+9+10+11+12+13+14+15 = 92
  //
  // out[12] =                   9+10+11+12+13+14+15 = 84  PHASE 4
  // out[13] =                     10+11+12+13+14+15 = 75  PHASE 4
  // out[14] =                        11+12+13+14+15 = 65
  // out[15] =                           12+13+14+15 = 54
  // ----------------------------------------------------------------

  public static void box1DFloat(
    float[] invec,
    int     inStartOffset,
    float[] outvec,
    int     outStartOffset,
    int     vectorLength,
    int     stride,
    int     fullWindowSize)
  {
    int halfWindowSize = (fullWindowSize+2)/2; // 7->4, 8->5

    int phase_1_nreps = halfWindowSize - 1;
    int phase_2_nreps = fullWindowSize - halfWindowSize + 1;
    int phase_3_nreps = vectorLength - fullWindowSize;
    int phase_4_nreps = halfWindowSize - 1;

    int li = 0; // Index of left edge of read window, for subtracts
    int ri = 0; // Index of right edge of read windows, for adds
    int oi = 0; // Index into output vector

    float sum = (float)0.0;
    int currentWindowSize = 0;

    // PHASE 1: ACCUMULATE FIRST SUM NO WRITES
    for (int i = 0; i < phase_1_nreps; i++) {
      sum += invec[inStartOffset + ri];
      currentWindowSize++;
      ri += stride;
    }

    // PHASE 2: INITIAL WRITES WITH SMALL WINDOW
    for (int i = 0; i < phase_2_nreps; i++) {
      sum += invec[inStartOffset + ri];
      currentWindowSize++;
      outvec[outStartOffset + oi] = sum / currentWindowSize;
      ri += stride;
      oi += stride;
    }

    // PHASE 3: WRITES WITH FULL WINDOW
    for (int i = 0; i < phase_3_nreps; i++) {
      sum += invec[inStartOffset + ri];
      sum -= invec[inStartOffset + li];
      outvec[outStartOffset + oi] = sum / currentWindowSize;
      li += stride;
      ri += stride;
      oi += stride;
    }

    // PHASE 4: FINAL WRITES WITH SMALL WINDOW
    for (int i = 0; i < phase_4_nreps; i++) {
      sum -= invec[inStartOffset + li];
      currentWindowSize--;
      outvec[outStartOffset + oi] = sum / currentWindowSize;
      li += stride;
      oi += stride;
    }
  }

  // ----------------------------------------------------------------
  public static void boxAlongRowsFloat(
    float[] in, // matrix as numRows x numCols in row-major order
    float[] out, // matrix as numRows x numCols in row-major order
    int numRows,
    int numCols,
    int windowSize
  ) {
    for (int i = 0; i < numRows; i++) {
      box1DFloat(in, i * numCols, out, i * numCols, numCols, 1, windowSize);
    }
  }

  // ----------------------------------------------------------------
  public static void boxAlongColsFloat(
    float[] in, // matrix as numRows x numCols in row-major order
    float[] out, // matrix as numRows x numCols in row-major order
    int numRows,
    int numCols,
    int windowSize
  ) {
    for (int j = 0; j < numCols; j++) {
      box1DFloat(in, j, out, j, numRows, numCols, windowSize);
    }
  }
}
