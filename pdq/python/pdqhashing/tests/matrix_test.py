# pyre-strict
# Copyright (c) Meta Platforms, Inc. and affiliates.
from pdqhashing.utils.matrix import MatrixUtil
import unittest


class MatrixTest(unittest.TestCase):
    def test_torben(self) -> None:
        numRows = 4
        numCols = 8
        matrix = MatrixUtil.allocateMatrix(numRows, numCols)
        for i in range(numRows):
            for j in range(numCols):
                matrix[i][j] = i + float((j * 0.01))
        self.assertEqual(MatrixUtil.torben(matrix, numRows, numCols), 1.07)
