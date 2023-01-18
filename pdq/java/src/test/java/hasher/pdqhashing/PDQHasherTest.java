// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

package hasher.pdqhashing;

import org.testng.Assert;
import org.testng.annotations.Test;
import pdqhashing.hasher.PDQHasher;
import pdqhashing.types.HashAndQuality;
import pdqhashing.utils.MatrixUtil;

import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.color.ColorSpace;
import java.awt.image.BufferedImage;
import java.awt.image.ColorConvertOp;
import java.io.File;

public class PDQHasherTest {
    @Test
    public void testFromBufferedImage() throws Exception {
        BufferedImage bi = ImageIO.read(new File("../data/reg-test-input/dih/bridge-1-original.jpg"));

        int numRows = bi.getHeight();
        int numCols = bi.getWidth();
        float[] buffer1 = MatrixUtil.allocateMatrixAsRowMajorArray(numRows, numCols);
        float[] buffer2 = MatrixUtil.allocateMatrixAsRowMajorArray(numRows, numCols);
        float[][] buffer64x64 = MatrixUtil.allocateMatrix(64, 64);
        float[][] buffer16x64 = MatrixUtil.allocateMatrix(16, 64);
        float[][] buffer16x16 = MatrixUtil.allocateMatrix(16, 16);

        PDQHasher hasher = new PDQHasher();
        HashAndQuality hashAndQuality = hasher.fromBufferedImage(bi, buffer1, buffer2, buffer64x64, buffer16x64, buffer16x16);

        Assert.assertEquals(hashAndQuality.getHash().toString(), "f8f8f0cee0f4a84f06370a22038f63f0b36e2ed596621e1d33e6b39c4e9c9b22");
        Assert.assertEquals(hashAndQuality.getHash().hammingDistance(hashAndQuality.getHash()), 0);

        BufferedImage bi2 = ImageIO.read(new File("../data/reg-test-input/dih/bridge-2-rotate-90.jpg"));
        numRows = bi2.getHeight();
        numCols = bi2.getWidth();
        buffer1 = MatrixUtil.allocateMatrixAsRowMajorArray(numRows, numCols);
        buffer2 = MatrixUtil.allocateMatrixAsRowMajorArray(numRows, numCols);
        buffer64x64 = MatrixUtil.allocateMatrix(64, 64);
        buffer16x64 = MatrixUtil.allocateMatrix(16, 64);
        buffer16x16 = MatrixUtil.allocateMatrix(16, 16);

        HashAndQuality hashAndQuality2 = hasher.fromBufferedImage(bi2, buffer1, buffer2, buffer64x64, buffer16x64, buffer16x16);

        Assert.assertEquals(hashAndQuality2.getHash().toString(), "30a10efd71cc3d429013d48d0ffffc52e34e0e17ada952a9d29685211ea9e5af");

        Assert.assertEquals(hashAndQuality.getHash().hammingDistance(hashAndQuality2.getHash()), 120);

        BufferedImage bi3 = ImageIO.read(new File("../data/reg-test-input/pen-and-coaster.png"));
        numRows = bi3.getHeight();
        numCols = bi3.getWidth();
        buffer1 = MatrixUtil.allocateMatrixAsRowMajorArray(numRows, numCols);
        buffer2 = MatrixUtil.allocateMatrixAsRowMajorArray(numRows, numCols);
        buffer64x64 = MatrixUtil.allocateMatrix(64, 64);
        buffer16x64 = MatrixUtil.allocateMatrix(16, 64);
        buffer16x16 = MatrixUtil.allocateMatrix(16, 16);

        HashAndQuality hashAndQuality3 = hasher.fromBufferedImage(bi3, buffer1, buffer2, buffer64x64, buffer16x64, buffer16x16);
        Assert.assertEquals(hashAndQuality.getHash().hammingDistance(hashAndQuality3.getHash()), 138);

        // try with gray-scaled image
        ColorSpace cs = ColorSpace.getInstance(ColorSpace.CS_GRAY);
        ColorConvertOp op = new ColorConvertOp(cs, null);
        BufferedImage bi_gs = op.filter(bi, null);

        numRows = bi_gs.getHeight();
        numCols = bi_gs.getWidth();
        buffer1 = MatrixUtil.allocateMatrixAsRowMajorArray(numRows, numCols);
        buffer2 = MatrixUtil.allocateMatrixAsRowMajorArray(numRows, numCols);
        buffer64x64 = MatrixUtil.allocateMatrix(64, 64);
        buffer16x64 = MatrixUtil.allocateMatrix(16, 64);
        buffer16x16 = MatrixUtil.allocateMatrix(16, 16);

        HashAndQuality hashAndQuality4 = hasher.fromBufferedImage(bi_gs, buffer1, buffer2, buffer64x64, buffer16x64, buffer16x16);
        Assert.assertEquals(hashAndQuality.getHash().hammingDistance(hashAndQuality4.getHash()), 0);

        // try with lower resolution image
        numRows = bi.getHeight();
        numCols = bi.getWidth();
        buffer1 = MatrixUtil.allocateMatrixAsRowMajorArray(numRows, numCols);
        buffer2 = MatrixUtil.allocateMatrixAsRowMajorArray(numRows, numCols);
        buffer64x64 = MatrixUtil.allocateMatrix(64, 64);
        buffer16x64 = MatrixUtil.allocateMatrix(16, 64);
        buffer16x16 = MatrixUtil.allocateMatrix(16, 16);
        BufferedImage bi_lowres = new BufferedImage(numCols/2, numRows/2, bi.getType());

        // scales the input image to the output image
        Graphics2D g2d = bi_lowres.createGraphics();
        g2d.drawImage(bi, 0, 0, numCols/2, numRows/2, null);
        g2d.dispose();

        HashAndQuality hashAndQuality5 = hasher.fromBufferedImage(bi_lowres, buffer1, buffer2, buffer64x64, buffer16x64, buffer16x16);
        Assert.assertEquals(hashAndQuality.getHash().hammingDistance(hashAndQuality5.getHash()), 4);
    }

}
