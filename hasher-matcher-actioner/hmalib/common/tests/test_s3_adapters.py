# Copyright (c) Meta Platforms, Inc. and affiliates.

from unittest import TestCase, skip

from hmalib.common.s3_adapters import ThreatUpdateS3Store, KNOWN_SIGNAL_TYPES

from hmalib.common.tests.mapping_common import get_default_signal_type_mapping


class S3AdaptersTestCase(TestCase):
    @skip("signal_type.INDICATOR_TYPE is no longer a string")
    def test_key_indicator_type_mapping(self):
        for signal_type in KNOWN_SIGNAL_TYPES:
            store = ThreatUpdateS3Store(
                1,
                1,
                None,
                "does-not-matter",
                "does-not-matter",
                "does-not-matter",
                KNOWN_SIGNAL_TYPES,
                signal_type_mapping=get_default_signal_type_mapping(),
            )

            assert signal_type == ThreatUpdateS3Store.get_signal_type_from_object_key(
                store.get_s3_object_key(signal_type.INDICATOR_TYPE)
            )
