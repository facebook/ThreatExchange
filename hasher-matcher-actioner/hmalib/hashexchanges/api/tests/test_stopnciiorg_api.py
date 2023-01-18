# Copyright (c) Meta Platforms, Inc. and affiliates.

import os
import unittest
import collections.abc

from hmalib.hashexchanges.api.stopnciiorg import StopNciiOrgAPI
from hmalib.hashexchanges.api.stopnciiorg_representations import HashRecord

X_FUNCTIONS_KEY = os.getenv("X_FUNCTIONS_KEY")

OCP_APIM_SUBSCRIPTION_KEY = os.getenv("OCP_APIM_SUBSCRIPTION_KEY")

STOPNCIIORG_BASE_URL = os.getenv("STOPNCIIORG_BASE_URL")


@unittest.skipUnless(
    X_FUNCTIONS_KEY and OCP_APIM_SUBSCRIPTION_KEY and STOPNCIIORG_BASE_URL,
    "Integration Test requires two api keys and a base url.",
)
class StopNciiOrgAPIIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.api = StopNciiOrgAPI(
            X_FUNCTIONS_KEY, OCP_APIM_SUBSCRIPTION_KEY, STOPNCIIORG_BASE_URL
        )

    def test_get_hashes(self):
        """
        Assumes that the response has at least one hash record.
        """
        response = self.api.get_hash_records_page(start_timestamp=0, page_size=10)
        #   test get_hash_records api from the very beginning to make sure we will get at least one record in the response.
        #   otherwise the test will fail.
        self.assertTrue(
            isinstance(response.hash_records, collections.abc.Sequence)
            and not isinstance(response, staticmethod),
            "hashRecords should be a list!",
        )

        self.assertTrue(isinstance(response.hash_records[0], HashRecord))
