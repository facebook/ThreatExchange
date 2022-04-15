# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import unittest

from threatexchange.content_type.photo import PhotoContent
from threatexchange.content_type.text import TextContent
from threatexchange.content_type.video import VideoContent
from threatexchange.signal_type.pdq import PdqSignal
from threatexchange.signal_type.raw_text import RawTextSignal
from threatexchange.signal_type.md5 import VideoMD5Signal

from hmalib.common.config import HMAConfig
from hmalib.common.models.tests.ddb_test_common import HMAConfigTestBase
from hmalib.common.mappings import (
    HMASignalTypeMapping,
)


class SignalTypeMappingInitTestCase(HMAConfigTestBase, unittest.TestCase):
    def test_bootstrapped_values_work(self):
        with self.fresh_dynamodb():
            HMAConfig.initialize(self.__class__.table.table_name)
            first_response = HMASignalTypeMapping.get_from_config_or_default()
            second_response = HMASignalTypeMapping.get_from_config_or_default()

            # Check that the first and second responses are the same.
            self.assertEqual(
                first_response.content_by_name, second_response.content_by_name
            )
            self.assertEqual(
                first_response.signal_type_by_name, second_response.signal_type_by_name
            )

    def test_config_writes_work(self):
        with self.fresh_dynamodb():
            HMAConfig.initialize(self.__class__.table.table_name)
            mapping = HMASignalTypeMapping(
                # Intentionally not using video md5, because that will be asserted as removed.
                # RawTextSignal is not present in default configs.
                signal_types=[PdqSignal, RawTextSignal],
                # Intentionally not using video, because that will be asserted as removed.
                # TextContent is not presend in default configs.
                content_types=[PhotoContent, TextContent],
            )

            mapping.write_as_configs()

            mappings_from_db = HMASignalTypeMapping.get_from_config_or_default()

            # Call enforce for types that must exists. Would raise ValueError in
            # case not found.
            mappings_from_db.get_content_type_enforce(TextContent.get_name())
            mappings_from_db.get_content_type_enforce(PhotoContent.get_name())

            mappings_from_db.get_signal_type_enforce(RawTextSignal.get_name())
            mappings_from_db.get_signal_type_enforce(PdqSignal.get_name())

            # Assert that video and videomd5 are not found.
            with self.assertRaises(ValueError):
                mappings_from_db.get_content_type_enforce(VideoContent.get_name()),
            with self.assertRaises(ValueError):
                mappings_from_db.get_signal_type_enforce(VideoMD5Signal.get_name()),
