# Copyright (c) Meta Platforms, Inc. and affiliates.

import numpy as np
from threatexchange.signal_type.pdq.pdq_hash_rotations import PDQHashRotations, RotationType

class TestPDQHashRotations:
    SAMPLE_HASH = "f8f8f0cee0f4a84f06370a22038f63f0b36e2ed596621e1d33e6b39c4e9c9b22"
    
    def test_hash_to_matrix_conversion(self):
        """Test conversion between hash string and matrix"""
        original_hash = self.SAMPLE_HASH
        matrix = PDQHashRotations._hash_to_matrix(original_hash)
        recovered_hash = PDQHashRotations._matrix_to_hash(matrix)
        assert original_hash == recovered_hash
        assert matrix.shape == (16, 16)
        assert np.all((matrix == 0) | (matrix == 1))

    def test_matrix_properties(self):
        """Test basic properties of the conversion matrix"""
        matrix = PDQHashRotations._hash_to_matrix(self.SAMPLE_HASH)
        assert matrix.dtype == np.float64
        assert matrix.shape == (16, 16)
        assert np.all(np.logical_or(matrix == 0, matrix == 1))

    def test_rotation_90(self):
        """Test 90-degree rotation properties"""
        matrix = PDQHashRotations._hash_to_matrix(self.SAMPLE_HASH)
        rotated = PDQHashRotations.rotate90(matrix)
        assert rotated.shape == (16, 16)
        # Test that applying rotation 4 times returns to original
        rotated_4x = matrix
        for _ in range(4):
            rotated_4x = PDQHashRotations.rotate90(rotated_4x)
        assert np.allclose(matrix, rotated_4x)

    def test_rotation_180(self):
        """Test 180-degree rotation properties"""
        matrix = PDQHashRotations._hash_to_matrix(self.SAMPLE_HASH)
        rotated = PDQHashRotations.rotate180(matrix)
        assert rotated.shape == (16, 16)
        # Test that applying rotation twice returns to original
        rotated_2x = PDQHashRotations.rotate180(rotated)
        assert np.allclose(matrix, rotated_2x)

    def test_rotation_270(self):
        """Test 270-degree rotation properties"""
        matrix = PDQHashRotations._hash_to_matrix(self.SAMPLE_HASH)
        rotated = PDQHashRotations.rotate270(matrix)
        assert rotated.shape == (16, 16)
        # Test that rotate270 is equivalent to three rotate90s
        rotated_90_3x = matrix
        for _ in range(3):
            rotated_90_3x = PDQHashRotations.rotate90(rotated_90_3x)
        assert np.allclose(rotated, rotated_90_3x)

    def test_flip_operations(self):
        """Test various flip operations"""
        matrix = PDQHashRotations._hash_to_matrix(self.SAMPLE_HASH)
        
        # Test flipx
        flipped_x = PDQHashRotations.flipx(matrix)
        assert flipped_x.shape == (16, 16)
        flipped_x_2x = PDQHashRotations.flipx(flipped_x)
        assert np.allclose(matrix, flipped_x_2x)
        
        # Test flipy
        flipped_y = PDQHashRotations.flipy(matrix)
        assert flipped_y.shape == (16, 16)
        flipped_y_2x = PDQHashRotations.flipy(flipped_y)
        assert np.allclose(matrix, flipped_y_2x)
        
        # Test flipplus1 
        flipped_plus = PDQHashRotations.flipplus1(matrix)
        assert flipped_plus.shape == (16, 16)
        flipped_plus_2x = PDQHashRotations.flipplus1(flipped_plus)
        assert np.allclose(matrix, flipped_plus_2x)
        
        # Test flipminus1
        flipped_minus = PDQHashRotations.flipminus1(matrix)
        assert flipped_minus.shape == (16, 16)
        flipped_minus_2x = PDQHashRotations.flipminus1(flipped_minus)
        assert np.allclose(matrix, flipped_minus_2x)

    def test_try_all_rotation(self):
        """Test the try_all_rotation method"""
        rotated_hashes = PDQHashRotations._try_all_rotation(self.SAMPLE_HASH)
        
        # Check that all rotation types are present
        assert set(rotated_hashes.keys()) == set(RotationType)
        
        # Check that original hash is preserved
        assert rotated_hashes[RotationType.ORIGINAL] == self.SAMPLE_HASH
        
        # Check that all rotated hashes are valid PDQ hashes
        for _, rotated_hash in rotated_hashes.items():
            if isinstance(rotated_hash, str):
                assert len(rotated_hash) == 64
                assert all(c in '0123456789abcdef' for c in rotated_hash)