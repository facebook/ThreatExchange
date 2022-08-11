# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import unittest
from threatexchange.exchanges.clients import ncmec
from threatexchange.exchanges.clients.ncmec.hash_api import NCMECEnvironment

from threatexchange.exchanges.impl.fb_threatexchange_api import (
    FBThreatExchangeCollabConfig,
)
from threatexchange.exchanges.impl.ncmec_api import (
    NCMECCollabConfig,
)


from hmalib.common.models.tests.ddb_test_common import HMAConfigTestBase
from hmalib.common.configs import tx_collab_config


class TXCollabConfigsTestCase(HMAConfigTestBase, unittest.TestCase):
    TABLE_NAME = f"test-config-{__name__}"

    def test_get_no_collab_config(self):
        with self.fresh_dynamodb():
            self.assertEqual([], tx_collab_config.get_all_collab_configs())

    def test_write_one_config(self):
        with self.fresh_dynamodb():
            tx_collab_config.create_collab_config(
                FBThreatExchangeCollabConfig(
                    name="Threatcollaboration Something", privacy_group=1212312
                )
            )
            all_configs = tx_collab_config.get_all_collab_configs()
            self.assertEqual(1, len(all_configs))
            self.assertEqual("Threatcollaboration Something", all_configs[0].name)
            self.assertEqual(1212312, all_configs[0].privacy_group)

    def test_write_and_retrieve(self):
        with self.fresh_dynamodb():
            tx_collab_config.create_collab_config(
                FBThreatExchangeCollabConfig(
                    name="Threatcollaboration Something", privacy_group=1212312
                )
            )
            config = tx_collab_config.get_collab_config(
                name="Threatcollaboration Something"
            )
            self.assertEqual("Threatcollaboration Something", config.name)
            self.assertEqual(1212312, config.privacy_group)

    def test_write_and_update(self):
        with self.fresh_dynamodb():
            tx_collab_config.create_collab_config(
                FBThreatExchangeCollabConfig(
                    name="Threatcollaboration Something", privacy_group=1212312
                )
            )
            config = tx_collab_config.get_collab_config(
                name="Threatcollaboration Something"
            )
            self.assertEqual("Threatcollaboration Something", config.name)
            self.assertEqual(1212312, config.privacy_group)

            # Now update
            config.privacy_group = 444333
            tx_collab_config.update_collab_config(config)

            config = tx_collab_config.get_collab_config(
                name="Threatcollaboration Something"
            )
            self.assertEqual(444333, config.privacy_group)

    def test_write_multiple_configs(self):
        with self.fresh_dynamodb():
            tx_collab_config.create_collab_config(
                FBThreatExchangeCollabConfig(
                    name="ThreatCollaboration something", privacy_group=121344
                ),
            )

            tx_collab_config.create_collab_config(
                FBThreatExchangeCollabConfig(
                    name="ThreatCollaboration something else", privacy_group=678876
                )
            )

            tx_collab_config.create_collab_config(
                NCMECCollabConfig(
                    name="child-safety",
                    environment=NCMECEnvironment.Exploitative,
                    only_esp_ids={1, 2, 3},
                )
            )

            all_configs = tx_collab_config.get_all_collab_configs()
            self.assertEqual(3, len(all_configs))

            ncmec_config = next(
                iter(
                    [
                        conf
                        for conf in all_configs
                        if isinstance(conf, NCMECCollabConfig)
                    ]
                )
            )
            self.assertEqual(ncmec_config.environment, NCMECEnvironment.Exploitative)
            self.assertEqual(ncmec_config.only_esp_ids, {1, 2, 3})
            self.assertEqual(ncmec_config.name, "child-safety")
