# Copyright (c) Meta Platforms, Inc. and affiliates.

import pytest
from threatexchange.signal_type.url_md5 import UrlMD5Signal

URL_TEST = "www.facebook.com/?user=123"
FULL_URL_TEST = "https://www.facebook.com/?user=123"
URL_TEST_MD5 = "e359430911fe80c2dd526d3cca21da30"


def test_can_hash_simple_url():
    assert (
        UrlMD5Signal.hash_from_str(URL_TEST) == URL_TEST_MD5
    ), "MD5 hash does not match"


def test_can_hash_full_url():
    assert (
        UrlMD5Signal.hash_from_str(FULL_URL_TEST) == URL_TEST_MD5
    ), "MD5 hash does not match"
