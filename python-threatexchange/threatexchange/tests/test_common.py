# Copyright (c) Meta Platforms, Inc. and affiliates.

import unittest

import threatexchange.common


class TestCommon(unittest.TestCase):
    def test_camel_case_to_underscore(self):
        assert threatexchange.common.camel_case_to_underscore("AbcXyz") == "abc_xyz"
