# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import os
import unittest
import collections.abc

from hmalib.hashexchanges.api.non_threatexchange_api import NonThreatExchangeAPI
from hmalib.hashexchanges.api.non_threatexchange_api_representations import HashRecord

X_FUNCTIONS_KEY = os.getenv("X_FUNCTIONS_KEY")

OCP_APIM_SUBSCRIPTION_KEY = os.getenv("OCP_APIM_SUBSCRIPTION_KEY")

BASE_NON_THREATEXCHANGE_URL = os.getenv("BASE_NON_THREATEXCHANGE_URL")


@unittest.skipUnless(
    X_FUNCTIONS_KEY and OCP_APIM_SUBSCRIPTION_KEY and BASE_NON_THREATEXCHANGE_URL,
    "Integration Test requires two api keys and a base url.",
)
class NonThreatExchangeAPIIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.api = NonThreatExchangeAPI(
            X_FUNCTIONS_KEY, OCP_APIM_SUBSCRIPTION_KEY, BASE_NON_THREATEXCHANGE_URL
        )

    def test_get_hashes(self):
        """
        Assumes that the response has at least one hash record.
        """
        response = self.api.get_hash_records(start_timestamp=0, page_size=10)
        #   test get_hash_records api from the very beginning to make sure we will get at least one record in the response.
        #   otherwise the test will fail.
        self.assertTrue(
            isinstance(response.hashRecords, collections.abc.Sequence)
            and not isinstance(response, staticmethod),
            "hashRecords should be a list!",
        )

        self.assertTrue(isinstance(response.hashRecords[0], HashRecord))
