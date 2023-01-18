#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import tempfile

from facebook import pdq
from libfb.py import testutil
from PIL import Image, ImageDraw


class TestHashing(testutil.BaseFacebookTestCase):
    def _get_test_image(self, width: int = 64, height: int = 64) -> Image:
        img = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(img)
        draw.pieslice((0, 0, width, height), 0, 45)
        draw.pieslice((0, 0, width, height), 90, 135)
        return img

    def test_jpg_image(self):
        _, name = tempfile.mkstemp(suffix=".jpg")
        self._get_test_image().save(name, "JPEG")
        hash, quality = pdq.get_hash(name)
        self.assertEqual(len(hash), 16)
        self.assertGreaterEqual(quality, 0)

    def test_png_image(self):
        _, name = tempfile.mkstemp(suffix=".png")
        self._get_test_image().save(name, "PNG")
        hash, quality = pdq.get_hash(name)
        self.assertEqual(len(hash), 16)
        self.assertGreaterEqual(quality, 0)

    def test_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            pdq.get_hash("not_a_file.png")

    def test_bad_args(self):
        with self.assertRaises(ValueError):
            pdq.get_hash(1, 2, 3)

    def test_hash_distance(self):
        _, name = tempfile.mkstemp(suffix=".png")
        self._get_test_image().save(name, "PNG")
        hash, _ = pdq.get_hash(name)
        dist_to_zero = pdq.distance(hash, [0] * len(hash))
        self.assertEqual(pdq.distance(hash, hash), 0)
        self.assertNotEqual(dist_to_zero, 0)
        self.assertEqual(dist_to_zero, pdq.norm(hash))

    def test_all_hashes(self):
        _, name = tempfile.mkstemp(suffix=".png")
        self._get_test_image().save(name, "PNG")
        (
            hash_normal,
            hash_rotate_90,
            hash_rotate_180,
            hash_rotate_270,
            hash_left_right,
            hash_top_bottom,
            hash_transpose,
            hash_transverse,
            quality,
        ) = pdq.get_all_hashes(name)
        all_hashes = [
            hash_normal,
            hash_rotate_90,
            hash_rotate_180,
            hash_rotate_270,
            hash_left_right,
            hash_top_bottom,
            hash_transpose,
            hash_transverse,
        ]
        self.assertGreaterEqual(quality, 0)
        for h in all_hashes:
            dist_to_zero = pdq.distance(h, [0] * len(h))
            self.assertEqual(pdq.distance(h, h), 0)
            self.assertNotEqual(dist_to_zero, 0)
            self.assertEqual(dist_to_zero, pdq.norm(h))
