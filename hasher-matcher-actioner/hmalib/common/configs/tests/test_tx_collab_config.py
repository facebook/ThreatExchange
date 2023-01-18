# Copyright (c) Meta Platforms, Inc. and affiliates.

import unittest
from uuid import uuid4
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
            bank_id = uuid4().hex

            tx_collab_config.create_collab_config(
                FBThreatExchangeCollabConfig(
                    name="Threatcollaboration Something", privacy_group=1212312
                ),
                import_as_bank_id=bank_id,
            )
            all_configs = [
                c.to_pytx_collab_config()
                for c in tx_collab_config.get_all_collab_configs()
            ]
            self.assertEqual(1, len(all_configs))
            self.assertEqual("Threatcollaboration Something", all_configs[0].name)
            self.assertEqual(1212312, all_configs[0].privacy_group)

    def test_write_and_retrieve(self):
        with self.fresh_dynamodb():
            bank_id = uuid4().hex

            tx_collab_config.create_collab_config(
                FBThreatExchangeCollabConfig(
                    name="Threatcollaboration Something", privacy_group=1212312
                ),
                import_as_bank_id=bank_id,
            )
            config = tx_collab_config.get_collab_config(
                name="Threatcollaboration Something"
            ).to_pytx_collab_config()

            self.assertEqual("Threatcollaboration Something", config.name)
            self.assertEqual(1212312, config.privacy_group)

    def test_write_and_update(self):
        with self.fresh_dynamodb():
            bank_id = uuid4().hex

            tx_collab_config.create_collab_config(
                FBThreatExchangeCollabConfig(
                    name="Threatcollaboration Something", privacy_group=1212312
                ),
                import_as_bank_id=bank_id,
            )
            config = tx_collab_config.get_collab_config(
                name="Threatcollaboration Something"
            ).to_pytx_collab_config()
            self.assertEqual("Threatcollaboration Something", config.name)
            self.assertEqual(1212312, config.privacy_group)

            # Now update
            config.privacy_group = 444333
            tx_collab_config.update_collab_config(config)

            config = tx_collab_config.get_collab_config(
                name="Threatcollaboration Something"
            ).to_pytx_collab_config()
            self.assertEqual(444333, config.privacy_group)

    def test_write_multiple_configs(self):
        with self.fresh_dynamodb():
            bank_id = uuid4().hex

            tx_collab_config.create_collab_config(
                FBThreatExchangeCollabConfig(
                    name="ThreatCollaboration something", privacy_group=121344
                ),
                import_as_bank_id=bank_id,
            )

            tx_collab_config.create_collab_config(
                FBThreatExchangeCollabConfig(
                    name="ThreatCollaboration something else", privacy_group=678876
                ),
                import_as_bank_id=bank_id,
            )

            tx_collab_config.create_collab_config(
                NCMECCollabConfig(
                    name="child-safety",
                    environment=NCMECEnvironment.Exploitative,
                    only_esp_ids={1, 2, 3},
                ),
                import_as_bank_id=bank_id,
            )

            all_configs = [
                c.to_pytx_collab_config()
                for c in tx_collab_config.get_all_collab_configs()
            ]
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

    def test_create_with_bank_id(self):
        with self.fresh_dynamodb():
            bank_id = uuid4().hex
            tx_collab_config.create_collab_config(
                FBThreatExchangeCollabConfig(
                    name="Threat Collaboration actually synced", privacy_group=21
                ),
                import_as_bank_id=bank_id,
            )

            config = tx_collab_config.get_collab_config(
                "Threat Collaboration actually synced"
            )
            self.assertEqual(config.import_as_bank_id, bank_id)

    def test_update_with_bank_id(self):
        with self.fresh_dynamodb():
            bank_id = uuid4().hex
            tx_collab_config.create_collab_config(
                FBThreatExchangeCollabConfig(
                    name="Threat Collaboration actually synced", privacy_group=21
                ),
                import_as_bank_id=bank_id,
            )

            config = tx_collab_config.get_collab_config(
                "Threat Collaboration actually synced"
            )
            tx_collab_config.update_collab_config(
                config.to_pytx_collab_config(), import_as_bank_id=bank_id
            )

            config = tx_collab_config.get_collab_config(
                "Threat Collaboration actually synced"
            )
            self.assertEqual(config.import_as_bank_id, bank_id)
