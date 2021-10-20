# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import os
import unittest
import collections.abc

from threatexchange.api import NonThreatExchangeAPI
from threatexchange.api_representations import HashRecord

X_FUNCTIONS_KEY = os.getenv("X_FUNCTIONS_KEY")

OCP_APIM_SUBSCRIPTION_KEY = os.getenv("OCP_APIM_SUBSCRIPTION_KEY")


@unittest.skipUnless(
    X_FUNCTIONS_KEY,
    "Integration Test requires tokens. Use X_FUNCTIONS_KEY environment variable.",
)
class NonThreatExchangeAPIIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.api = NonThreatExchangeAPI(X_FUNCTIONS_KEY, OCP_APIM_SUBSCRIPTION_KEY, 0)

    def test_get_hashes(self):
        """
        Assumes that the response has at least one hash record.
        """
        response = self.api.get_hash_records()
        self.assertTrue(
            isinstance(response, collections.abc.Sequence)
            and not isinstance(response, staticmethod),
            "API returned something that's not a list!",
        )

        self.assertTrue(isinstance(response[0], HashRecord))
