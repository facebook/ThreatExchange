# Copyright (c) Meta Platforms, Inc. and affiliates.

import typing as t
from hmalib.common.external_api import BaseAPI
from hmalib.hashexchanges.api.stopnciiorg_representations import (
    HashRecordsPage,
)


class StopNciiOrgAPI(BaseAPI):
    """
    A client for the API hosted by StopNCII.org. Mostly mirrors ThreatExchange's
    functionality.
    """

    def __init__(
        self,
        x_functions_key: str,
        ocp_apim_subscription_key: str,
        base_url: str,
    ) -> None:
        self.x_functions_key = x_functions_key
        self.ocp_apim_subscription_key = ocp_apim_subscription_key
        self._base_url = base_url

    def get_hash_records_page(
        self,
        start_timestamp: int,
        page_size: int = 1000,
        next_page_token: str = None,
    ) -> HashRecordsPage:
        """
        Returns a paginated list of all hash records from start_timestamp.
        """

        params: t.Dict[str, t.Union[str, int]] = {
            "startTimestamp": start_timestamp,
            "pageSize": page_size,
        }
        if next_page_token is not None:
            params["nextPageToken"] = next_page_token
        url = super()._get_api_url("FetchHashes", params)
        headers = {
            "x-functions-key": self.x_functions_key,
            "Ocp-Apim-Subscription-Key": self.ocp_apim_subscription_key,
        }
        response = super().get_json_from_url(url=url, headers=headers)
        return HashRecordsPage.from_dict(response)
