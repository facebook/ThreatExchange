# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

from unittest import TestCase

from hmalib.common.s3_adapters import ThreatUpdateS3Store, KNOWN_SIGNAL_TYPES

from hmalib.common.models.tests.test_bank_member_signals_to_process import (
    TestHMASignalTypeConfigs,
)


class S3AdaptersTestCase(TestCase):
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
                signal_type_mapping=TestHMASignalTypeConfigs(),
            )

            assert signal_type == ThreatUpdateS3Store.get_signal_type_from_object_key(
                store.get_s3_object_key(signal_type.INDICATOR_TYPE)
            )
