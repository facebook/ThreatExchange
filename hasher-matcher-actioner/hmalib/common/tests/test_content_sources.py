# Copyright (c) Meta Platforms, Inc. and affiliates.

import unittest
import io

from PIL import Image
import requests.exceptions

from hmalib.common.content_sources import URLContentSource

FB_LOGO_URL = (
    "https://facebookbrand.com/wp-content/uploads/2019/04/f_logo_RGB-Hex-Blue_512.png"
)

HTTP_404_URL = "http://httpstat.us/404"


class URLContentSourceTestCase(unittest.TestCase):
    def test_get_known_image(self):
        # This can get flaky if the FB_LOGO URL changes, replace with a more
        # durable URL if you can find one.
        provider = URLContentSource()
        _bytes = provider.get_bytes(FB_LOGO_URL)

        self.assertIsNotNone(_bytes)

        # Try to create an image in PILLOW to ensure we are getting bytes that
        # are actually an image. Will throw an exception if magic bytes are
        image = Image.open(io.BytesIO(_bytes))

    def test_get_known_404(self):
        provider = URLContentSource()
        self.assertRaises(
            requests.exceptions.HTTPError, provider.get_bytes, HTTP_404_URL
        )
