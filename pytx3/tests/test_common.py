import unittest

import pytx3.common


class TestCommon(unittest.TestCase):
    def test_camel_case_to_underscore(self):
        assert pytx3.common.camel_case_to_underscore("AbcXyz") == "abc_xyz"
