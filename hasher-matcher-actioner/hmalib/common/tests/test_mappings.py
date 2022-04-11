# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import unittest

from hmalib.common.config import HMAConfig
from hmalib.common.models.tests.ddb_test_common import HMAConfigTestBase
from hmalib.common.mappings import (
    HMASignalTypeMapping,
    DEFAULT_SIGNAL_AND_CONTENT_TYPES,
    ToggleableContentTypeConfig,
)


class SignalTypeMappingInitTestCase(HMAConfigTestBase, unittest.TestCase):
    def test_first_call_to_HMASignalTypeMapping_creates_configs(self):
        with self.fresh_dynamodb():
            HMAConfig.initialize(self.__class__.table.table_name)
            first_response = HMASignalTypeMapping()

            # rely on internal details to verify that records actually got
            # created.
            self.assertNotEqual(ToggleableContentTypeConfig.get_all(), [])

            second_response = HMASignalTypeMapping()

            # Check that the first and second responses are the same.
            self.assertEqual(
                first_response.content_by_name, second_response.content_by_name
            )
            self.assertEqual(
                first_response.signal_type_by_name, second_response.signal_type_by_name
            )
