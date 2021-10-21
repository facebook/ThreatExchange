# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import typing as t
from .api_representations import HashRecord
from .api import ThreatExchangeAPI


class NonThreatExchangeAPI(ThreatExchangeAPI):

    def __init__(
        self,
        x_functions_key: str,
        ocp_apim_subscription_key: str,
        start_timestamp: int,
        base_url: str,
        *,
        page_size: int = 1000,
    ) -> None:
        self.x_functions_key = x_functions_key
        self.ocp_apim_subscription_key = ocp_apim_subscription_key
        self.start_timestamp = start_timestamp
        self.page_size = page_size
        self._base_url = base_url or self._BASE_URL

    def get_hash_records(
        self,
    ) -> t.List[HashRecord]:
        """
        Returns a paginated list of all hash records from start_timestamp.
        """

        params = {
            "startTimestamp": self.start_timestamp,
            "pageSize": self.page_size,
        }
        url = self._get_graph_api_url("FetchHashes", params)
        headers = {
            "x-functions-key": self.x_functions_key,
            "Ocp-Apim-Subscription-Key": self.ocp_apim_subscription_key,
        }
        response = self.get_json_from_url(url=url, headers=headers)
        return [HashRecord.from_dict(d) for d in response["hashRecords"]]
