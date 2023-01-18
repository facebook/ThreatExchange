# Copyright (c) Meta Platforms, Inc. and affiliates.

import unittest


from hmalib.common.config import HMAConfig
from hmalib.common.models.tests.ddb_test_common import HMAConfigTestBase
from hmalib.common.configs.tx_apis import (
    ToggleableSignalExchangeAPIConfig,
    set_status_signal_exchange_api,
    add_signal_exchange_api,
    AddSignalExchangeAPIResult,
)


class TXApiConfigsTestCase(HMAConfigTestBase, unittest.TestCase):
    TABLE_NAME = f"test-config-{__name__}"

    def test_get_all_empty(self):
        with self.fresh_dynamodb():
            self.assertEqual(ToggleableSignalExchangeAPIConfig.get_all(), [])

    def test_write_to_empty(self):
        with self.fresh_dynamodb():
            self.assertEqual(ToggleableSignalExchangeAPIConfig.get_all(), [])

            resp = add_signal_exchange_api(
                klass="threatexchange.exchanges.impl.fb_threatexchange_api.FBThreatExchangeSignalExchangeAPI"
            )
            self.assertEqual(resp, AddSignalExchangeAPIResult.ADDED)

            self.assertEqual(len(ToggleableSignalExchangeAPIConfig.get_all()), 1)

    def test_rewrite(self):
        with self.fresh_dynamodb():
            add_signal_exchange_api(
                klass="threatexchange.exchanges.impl.fb_threatexchange_api.FBThreatExchangeSignalExchangeAPI"
            )
            resp = add_signal_exchange_api(
                klass="threatexchange.exchanges.impl.fb_threatexchange_api.FBThreatExchangeSignalExchangeAPI"
            )
            self.assertEqual(resp, AddSignalExchangeAPIResult.ALREADY_EXISTS)
            self.assertEqual(len(ToggleableSignalExchangeAPIConfig.get_all()), 1)

    def test_fail(self):
        with self.fresh_dynamodb():
            resp = add_signal_exchange_api(
                klass="does.not.contain.class.FBThreatExchangeSignalExchangeAPI"
            )
            self.assertEqual(resp, AddSignalExchangeAPIResult.FAILED)

    def test_disable(self):
        with self.fresh_dynamodb():
            add_signal_exchange_api(
                "threatexchange.exchanges.impl.ncmec_api.NCMECCollabConfig"
            )

            self.assertTrue(ToggleableSignalExchangeAPIConfig.get_all()[0].enabled)
            set_status_signal_exchange_api(
                "threatexchange.exchanges.impl.ncmec_api.NCMECCollabConfig", False
            )
            self.assertFalse(ToggleableSignalExchangeAPIConfig.get_all()[0].enabled)
