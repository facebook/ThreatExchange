from contextlib import nested
from mock import patch
import pytest

from pytx import access_token
from pytx import ThreatDescriptor

class TestInit:
    def test_page_limit(self):
        """
        Don't see a way to test that it is actually sending this along,
        so this test just makes sure that the function call works as expected.

        Limit will still limit the total results, page_limit
        """
        try:
            access_token.init()
        except:
            #Need a valid access token for these tests.
            return

        page_limit = 10

        results = ThreatDescriptor.objects(type_='IP_ADDRESS',
                                           page_limit=page_limit,
                                           limit=5,
                                           text='proxy')
        num_of_results = 0

        for result in results:
            num_of_results += 1

        assert 5 == num_of_results