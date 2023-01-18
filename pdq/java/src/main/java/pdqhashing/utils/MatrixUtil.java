// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

package pdqhashing.utils;

public class MatrixUtil {

  public static float[][] allocateMatrix(int numRows, int numCols) {
    float[][] rv = new float[numRows][];
    for (int i = 0; i < numRows; i++) {
      rv[i] = new float[numCols];
    }
    return rv;
  }

  public static float[] allocateMatrixAsRowMajorArray(int numRows, int numCols) {
    return new float[numRows * numCols];
  }

  // Tester method
  public static void main(String[] args) {
    int numRows = 4;
    int numCols = 8;
    float[][] matrix = allocateMatrix(numRows, numCols);
    for (int i = 0; i < numRows; i++) {
      for (int j = 0; j < numCols; j++) {
        matrix[i][j] = i + (float)(j * 0.01);
      }
    }
    for (int i = 0; i < numRows; i++) {
      System.out.printf(" ");
      for (int j = 0; j < numCols; j++) {
        System.out.printf(" %6.3f", matrix[i][j]);
      }
      System.out.printf("\n");
    }
  }

  // ================================================================
  // The following code is public domain.
  // Algorithm by Torben Mogensen, implementation by N. Devillard.
  // This code in public domain.
  // C/array -> Java/matrix port: John Kerl
  // ================================================================

  /**
   * Torben's median algorithm.
   */
  public static float torben(float[][] m, int numRows, int numCols) {
    int n = numRows * numCols;
    int midn = (n + 1) / 2;

    int i, j, less, greater, equal;
    float min, max, guess, maxltguess, mingtguess;

    min = max = m[0][0];
    for (i = 0; i < numRows; i++) {
      for (j = 0; j < numCols; j++) {
        float v = m[i][j];
        if (v < min) min = v;
        if (v > max) max = v;
      }
    }

    while (true) {
      guess = (min + max)/2;
      less = 0; greater = 0; equal = 0;
      maxltguess = min;
      mingtguess = max;

      for (i = 0; i < numRows; i++) {
        for (j = 0; j < numCols; j++) {
          float v = m[i][j];
          if (v <guess) {
            less++;
            if (v > maxltguess) maxltguess = v;
          } else if (v > guess) {
            greater++;
            if (v < mingtguess) mingtguess = v;
          } else equal++;
        }
      }

      if (less <= midn && greater <= midn)
        break;
      else if (less>greater)
        max = maxltguess;
      else
        min = mingtguess;
    }
    if (less >= midn) {
      return maxltguess;
    } else if (less+equal >= midn) {
      return guess;
    } else {
      return mingtguess;
    }
  }
}
