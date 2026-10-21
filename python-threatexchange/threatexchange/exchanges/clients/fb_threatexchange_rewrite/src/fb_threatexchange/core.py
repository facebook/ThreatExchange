"""
Core functionality for the ThreatExchange client.
"""

from typing import Any, Dict, List, Optional
import os
import requests

from fb_threatexchange.models import (
    ThreatDescriptor,
    ThreatIndicator,
    ThreatExchangeMember,
)


class ThreatExchangeClient:
    """
    Client for interacting with the ThreatExchange API.

    This client provides methods to query, submit, and manage threat
    intelligence data through the ThreatExchange platform.

    Attributes:
        access_token: The access token for authentication.
        base_url: The base URL for the ThreatExchange API.
    """

    DEFAULT_BASE_URL = "https://graph.facebook.com"

    def __init__(self, access_token: Optional[str] = None, base_url: Optional[str] = None) -> None:
        """
        Initialize the ThreatExchange client.

        Args:
            access_token: Optional direct access token. If not provided,
                will be read from the `ACCESS_TOKEN` environment variable.
            base_url: Optional custom base URL for the API.
        """
        self.access_token = access_token or os.getenv("ACCESS_TOKEN")
        if not self.access_token:
            raise ValueError("ACCESS_TOKEN environment variable not set and no access_token provided")

        self.base_url = base_url or self.DEFAULT_BASE_URL

    def get_access_token(self) -> str:
        """
        Return the access token used for API authentication.

        Returns:
            The access token string.
        """
        return self.access_token
    
    def get_members(self) -> List[ThreatExchangeMember]:
        """
        Get the list of members in ThreatExchange

        Returns:
            A list of `ThreatExchangeMember` objects.
        """
        path = "threat_exchange_members"
        url = f"{self.base_url.rstrip('/')}/{path}"
        params = {"access_token": self.get_access_token()}

        try:
            resp = requests.get(url, params=params, timeout=10, headers={"Accept": "application/json"})
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            raise RuntimeError(f"Failed to fetch members from {url}: {exc}")

        # Normalize to a list of item dicts
        items: List[dict]
        if isinstance(data, dict) and "data" in data:
            items = data.get("data") or []
        elif isinstance(data, list):
            items = data
        else:
            items = [data]

        members: List[ThreatExchangeMember] = []
        for item in items:
            if not isinstance(item, dict):
                # skip unexpected entries
                continue
            members.append(ThreatExchangeMember.from_dict(item))

        return members
    

    def get_threat_descriptors(
        self,
        text: str,
        limit: int = 100,
        **kwargs: Any,
    ) -> List[ThreatDescriptor]:
        """
        Search for threat descriptors matching the given text.

        Args:
            text: The text to search for.
            limit: Maximum number of results to return.
            **kwargs: Additional query parameters.

        Returns:
            A list of ThreatDescriptor objects.
        """
        # Placeholder implementation
        return []

    def get_threat_indicators(
        self,
        descriptor_id: str,
    ) -> List[ThreatIndicator]:
        """
        Get threat indicators associated with a descriptor.

        Args:
            descriptor_id: The ID of the threat descriptor.

        Returns:
            A list of ThreatIndicator objects.
        """
        # Placeholder implementation
        return []

    def submit_descriptor(
        self,
        descriptor: ThreatDescriptor,
    ) -> Dict[str, Any]:
        """
        Submit a new threat descriptor to ThreatExchange.

        Args:
            descriptor: The ThreatDescriptor to submit.

        Returns:
            The API response as a dictionary.
        """
        # Placeholder implementation
        return {"success": True}

