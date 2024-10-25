# Copyright (c) Meta Platforms, Inc. and affiliates.

import numpy as np
from enum import Enum, auto

class RotationType(Enum):
    ORIGINAL = auto()
    ROTATE90 = auto()
    ROTATE180 = auto()
    ROTATE270 = auto()
    FLIPX = auto()
    FLIPY = auto()
    FLIPPLUS1 = auto()
    FLIPMINUS1 = auto()

class PDQHashRotations:
    @staticmethod
    def _hash_to_matrix(hash_str: str) -> np.ndarray:
        """Convert a 256-bit PDQ hash string to 16x16 float matrix."""
        # Convert hex string to binary
        binary = bin(int(hash_str, 16))[2:].zfill(256)
        # Convert to 16x16 matrix of floats
        return np.array([float(int(b)) for b in binary]).reshape(16, 16)
    
    @staticmethod
    def _matrix_to_hash(matrix: np.ndarray) -> str:
        """Convert 16x16 float matrix back to PDQ hash string."""
        # Flatten matrix and convert to binary string
        binary = ''.join(['1' if x > 0 else '0' for x in matrix.flatten()])
        # Convert to hex
        return hex(int(binary, 2))[2:].zfill(64)

    @classmethod 
    def rotate90(cls, matrix: np.ndarray) -> np.ndarray: 
        result = np.zeros((16, 16))
        for i in range(16):
            for j in range(16):
                result[i][j] = -matrix[i, j] if j & 1 else matrix[i, j]
        return result

    @classmethod
    def rotate180(cls, matrix: np.ndarray) -> np.ndarray:
        result = np.zeros((16, 16))
        for i in range(16):
            for j in range(16):
                result[i][j] = -matrix[i, j] if (i + j) & 1 else matrix[i, j]
        return result
    
    @classmethod
    def rotate270(cls, matrix: np.ndarray) -> np.ndarray:
        result = np.zeros((16, 16))
        for i in range(16):
            for j in range(16):
                result[j, i] = -matrix[i, j] if i & 1 else matrix[i, j]
        return result

    @classmethod
    def flipx(cls, matrix: np.ndarray) -> np.ndarray:
        result = np.zeros((16, 16))
        for i in range(16):
            for j in range(16):
                result[i, j] = -matrix[i, j] if i & 1 else matrix[i, j]
        return result
    
    @classmethod
    def flipy(cls, matrix: np.ndarray) -> np.ndarray:
        result = np.zeros((16, 16))
        for i in range(16):
            for j in range(16):
                result[i, j] = -matrix[i, j] if j & 1 else matrix[i, j]
        return result

    @classmethod
    def flipplus1(cls, matrix: np.ndarray) -> np.ndarray:
        return matrix.T

    @classmethod
    def flipminus1(cls, matrix: np.ndarray) -> np.ndarray:
        result = np.zeros((16, 16))
        for i in range(16):
            for j in range(16):
                result[j, i] = -matrix[i, j] if (i + j) & 1 else matrix[i, j]
        return result
    
    @classmethod
    def _try_all_rotation(cls, hash: str):
        matrix = cls._hash_to_matrix(hash)
        rotations = {
            RotationType.ORIGINAL: matrix,
            RotationType.ROTATE90: cls.rotate90(matrix),
            RotationType.ROTATE180: cls.rotate180(matrix),
            RotationType.ROTATE270: cls.rotate270(matrix),
            RotationType.FLIPX: cls.flipx(matrix),
            RotationType.FLIPY: cls.flipy(matrix),
            RotationType.FLIPPLUS1: cls.flipplus1(matrix),
            RotationType.FLIPMINUS1: cls.flipminus1(matrix)
        }
        rotated_hashes = {}
        for rotation_type, rotated_matrix in rotations.items():
            rotated_hash = cls._matrix_to_hash(rotated_matrix)
            rotated_hashes[rotation_type] = rotated_hash
        return rotated_hashes
