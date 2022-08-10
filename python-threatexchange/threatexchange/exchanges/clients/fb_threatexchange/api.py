# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
This is an entire copy of a file from ThreatExchange/hashing

TODO: Slim down to only what we need
"""

import copy
import json
import typing as t
import os
import pathlib
import re

import urllib.parse
import urllib.error

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


from .api_representations import ThreatPrivacyGroup


def is_valid_app_token(token: str) -> bool:
    """Returns true if the string looks like a valid token"""
    return bool(re.match("[0-9]{8,}(?:%7C|\\|)[a-zA-Z0-9_\\-]{20,}", token))


class TimeoutHTTPAdapter(HTTPAdapter):
    """
    Plug into requests to get a well-behaved session that does not wait for eternity.
    H/T: https://findwork.dev/blog/advanced-usage-python-requests-timeouts-retries-hooks/#setting-default-timeouts
    """

    def __init__(self, *args, timeout=5, **kwargs):
        self.timeout = timeout
        super().__init__(*args, **kwargs)

    def send(self, request, *, timeout=None, **kwargs):
        if timeout is None:
            timeout = self.timeout
        return super().send(request, timeout=timeout, **kwargs)


class _CursoredResponse:
    """Wrapper around paginated responses from Graph API"""

    def __init__(self, api: "ThreatExchangeAPI", url, params, decode_fn=None) -> None:
        self.api = api
        self.response = None
        self.next_url = url
        self.params = params
        self.data: t.List = []
        self.decode_fn = decode_fn

    @property
    def done(self):
        return self.next_url is None

    def next(self):
        if self.done:
            return []
        response = self.api.get_json_from_url(self.next_url, self.params)
        next_url = response.get("paging", {}).get("next")
        data = response.get("data", [])
        if self.decode_fn:
            data = [self.decode_fn(x) for x in data]
        self.next_url = next_url
        self.data = data
        self.params.clear()
        return self.data

    def __iter__(self):
        while not self.done:
            self.next()
            if self.data is not None:
                yield self.data


class ThreatExchangeAPI:
    _TE_BASE_URL = "https://graph.facebook.com/v9.0"

    # This is just a keystroke-saver / error-avoider for passing around
    # post-parameter field names.

    _POST_PARAM_NAMES = {
        "indicator": "indicator",  # For submit
        "type": "type",  # For submit
        "descriptor_id": "descriptor_id",  # For update
        "description": "description",
        "share_level": "share_level",
        "status": "status",
        "privacy_type": "privacy_type",
        "privacy_members": "privacy_members",
        "tags": "tags",
        "add_tags": "add_tags",
        "remove_tags": "remove_tags",
        "confidence": "confidence",
        "precision": "precision",
        "review_status": "review_status",
        "severity": "severity",
        "expired_on": "expired_on",
        "first_active": "first_active",
        "last_active": "last_active",
        "related_ids_for_upload": "related_ids_for_upload",
        "related_triples_for_upload_as_json": "related_triples_for_upload_as_json",
        # Legacy : should have been named reactions_to_add, but isn't. :(
        "reactions": "reactions",
        "reactions_to_remove": "reactions_to_remove",
    }

    def __init__(
        self,
        api_token: str,
        *,
        endpoint_override: t.Optional[str] = None,
    ) -> None:
        self.api_token = api_token
        self._base_url = endpoint_override or self._TE_BASE_URL

    @property
    def app_id(self):
        return int(self.api_token.partition("|")[0])

    def get_json_from_url(self, url, params=None, *, json_obj_hook: t.Callable = None):
        """
        Perform an HTTP GET request, and return the JSON response payload.
        Same timeouts and retry strategy as `_get_session` above.
        """
        with self._get_session() as _session:
            response = requests.get(url, params=params or {})  # !!! Typo? session.get?
            response.raise_for_status()
            return response.json(object_hook=json_obj_hook)

    def _get_session(self):
        """
        Custom requests sesson

        Ideally, should be used within a context manager:
        ```
        with self._get_session() as session:
            session.get()...
        ```

        If using without a context manager, ensure you end up calling close() on
        the returned value.
        """
        session = requests.Session()
        session.mount(
            self._base_url,
            adapter=TimeoutHTTPAdapter(
                timeout=60,
                max_retries=Retry(
                    total=4,
                    status_forcelist=[429, 500, 502, 503, 504],
                    allowed_methods=["HEAD", "GET", "OPTIONS"],
                    backoff_factor=0.2,  # ~1.5 seconds of retries
                ),
            ),
        )
        return session

    def get_tag_id(self, tagName, showURLs=False):
        """
        Looks up the "objective tag" ID for a given tag.
        This is suitable input for the /threat_tags endpoint.
        """
        url = (
            self._base_url
            + "/threat_tags"
            + "/?access_token="
            + self.api_token
            + "&text="
            + urllib.parse.quote(tagName)
        )
        if showURLs:
            print("URL:")
            print(url)

        response = self.get_json_from_url(url)

        # The lookup will get everything that has this as a prefix.
        # So we need to filter the results. This loop also handles the
        # case when the results array is empty.
        #
        # Example: when querying for "media_type_video", we want the 2nd one:
        # { "data": [
        #   { "id": "9999338563303771", "text": "media_type_video_long_hash" },
        #   { "id": "9999474908560728", "text": "media_type_video" },
        #   { "id": "9889872714202918", "text": "media_type_video_hash_long" }
        #   ], ...
        # }
        data = response["data"]
        desired = list(filter(lambda o: o["text"] == tagName, data))
        if len(desired) < 1:
            return None
        else:
            return desired[0]["id"]

    def get_threat_descriptors(self, ids, **kwargs):
        """
        Looks up all metadata for given IDs.
        """
        verbose = kwargs.get("verbose", False)
        showURLs = kwargs.get("showURLs", False)
        includeIndicatorInOutput = kwargs.get("includeIndicatorInOutput", True)

        default_fields = [
            "raw_indicator",
            "type",
            "added_on",
            "last_updated",
            "confidence",
            "owner",
            "privacy_type",
            "review_status",
            "status",
            "severity",
            "share_level",
            "tags",
            "description",
            "reactions",
            "my_reactions",
        ]
        fields = kwargs.get("fields", default_fields)

        # Check well-formattedness of descriptor IDs (which may have come from
        # arbitrary data on stdin).
        for id in ids:
            try:
                _ = int(id)
            except ValueError:
                raise Exception('Malformed descriptor ID "%s"' % id)

        # See also
        # https://developers.facebook.com/docs/threat-exchange/reference/apis/threat-descriptor/
        # for available fields

        url = (
            self._base_url
            + "/?access_token="
            + self.api_token
            + "&ids="
            + ",".join(ids)
            + "&fields="
            + ",".join(fields)
        )

        if showURLs:
            print("URL:")
            print(url)

        response = self.get_json_from_url(url)

        descriptors = []
        for id, descriptor in response.items():
            if not includeIndicatorInOutput:
                del descriptor["raw_indicator"]
            if verbose:
                print(json.dumps(descriptor))

            if "tags" in fields:
                # tags is returned as a dict sturctred like:
                # "tags": {
                #   "data": [
                #         {
                #            "id": "03465026013486502",
                #            "text": "uploaded_by_hma"
                #         }
                #      ]
                #   },
                #
                # Canonicalize the tag ordering and simplify the
                # structure to simply an array of tag-texts
                tags = descriptor.get("tags", {"data": []})["data"]
                descriptor["tags"] = sorted(tag["text"] for tag in tags)

            if descriptor.get("description") is None and "description" in fields:
                descriptor["description"] = ""

            descriptors.append(descriptor)
        return descriptors

    def get_threat_updates(
        self,
        privacy_group: int,
        *,
        start_time: t.Optional[int] = None,
        stop_time: t.Optional[int] = None,
        types: t.Iterable[str] = (),
        page_size: t.Optional[int] = None,
        fields: t.Optional[t.Iterable[str]] = None,
        decode_fn: t.Callable[[t.Any], t.Any] = None,
    ) -> _CursoredResponse:
        """Gets threat updates for the given privacy group."""

        if fields is None:
            fields = (
                "id",
                "indicator",
                "type",
                "creation_time",
                "last_updated",
                "should_delete",
                "tags",
                "status",
                "applications_with_opinions",
            )

        params = {
            "access_token": self.api_token,
            "start_time": start_time,
            "stop_time": stop_time,
            "limit": page_size,
            "fields": ",".join(fields),
        }
        if types:
            params["types"] = ",".join(types)

        url = f"{self._base_url}/{privacy_group}/threat_updates/"
        return _CursoredResponse(self, url, params, decode_fn=decode_fn)

    def get_privacy_group(self, id: int) -> ThreatPrivacyGroup:
        """
        Returns a non-paginated list of all privacy groups the current app is a
        member of.
        """
        fields = [
            "id",
            "members_can_see",
            "members_can_use",
            "name",
            "description",
            "last_updated",
            "added_on",
            "threat_updates_enabled",
        ]
        url = self._get_graph_api_url(f"{id}", {"fields": ",".join(fields)})
        response = self.get_json_from_url(url)
        return ThreatPrivacyGroup.from_graph_api_dict(response)

    def get_threat_privacy_groups_member(
        self,
    ) -> t.List[ThreatPrivacyGroup]:
        """
        Returns a non-paginated list of all privacy groups the current app is a
        member of.
        """
        fields = [
            "id",
            "members_can_see",
            "members_can_use",
            "name",
            "description",
            "last_updated",
            "added_on",
            "threat_updates_enabled",
        ]
        url = self._get_graph_api_url(
            f"{self.app_id}/threat_privacy_groups_member", {"fields": ",".join(fields)}
        )
        response = self.get_json_from_url(url)
        return [ThreatPrivacyGroup.from_graph_api_dict(d) for d in response["data"]]

    def get_threat_privacy_groups_owner(
        self,
    ) -> t.List[ThreatPrivacyGroup]:
        """
        Returns a non-paginated list of all privacy groups the current app is a
        owner of.
        """
        fields = [
            "id",
            "members_can_see",
            "members_can_use",
            "name",
            "description",
            "last_updated",
            "added_on",
            "threat_updates_enabled",
        ]
        url = self._get_graph_api_url(
            f"{self.app_id}/threat_privacy_groups_owner", {"fields": ",".join(fields)}
        )
        response = self.get_json_from_url(url)
        return [ThreatPrivacyGroup.from_graph_api_dict(d) for d in response["data"]]

    def _get_graph_api_url(
        self, sub_path: t.Optional[str], query_dict: t.Dict = {}
    ) -> str:
        """
        Returns a threatexchange URL for a sub-path and a dictionary of query
        parameters. Automatically adds access_token to the query dictionary.
        """
        if "access_token" not in query_dict:
            query_dict["access_token"] = self.api_token

        query = urllib.parse.urlencode(query_dict)

        base_url_parts = urllib.parse.urlparse(self._base_url)
        url_parts = urllib.parse.ParseResult(
            base_url_parts.scheme,
            base_url_parts.netloc,
            f"{base_url_parts.path}/{sub_path}",
            base_url_parts.params,
            query,
            base_url_parts.fragment,
        )

        return urllib.parse.urlunparse(url_parts)

    def _validate_post_params_for_submit(self, postParams):
        """
        Returns error message or None.
        This simply checks to see (client-side) if required fields aren't provided.
        """
        if postParams.get(self._POST_PARAM_NAMES["descriptor_id"]) != None:
            return "descriptor_id must not be specified for submit."

        requiredFields = [
            self._POST_PARAM_NAMES["indicator"],
            self._POST_PARAM_NAMES["type"],
            self._POST_PARAM_NAMES["description"],
            self._POST_PARAM_NAMES["share_level"],
            self._POST_PARAM_NAMES["status"],
            self._POST_PARAM_NAMES["privacy_type"],
        ]

        missingFields = [
            fieldName if postParams.get(fieldName) == None else None
            for fieldName in requiredFields
        ]
        missingFields = [fieldName for fieldName in missingFields if fieldName != None]

        if len(missingFields) == 0:
            return None
        elif len(missingFields) == 1:
            return "Missing field %s" % missingFields[0]
        else:
            return "Missing fields %s" % ",".join(missingFields)

    def _validate_post_pararms_for_copy(self, postParams):
        """
        Returns error message or None.
        This simply checks to see (client-side) if required fields aren't provided.
        """
        if postParams.get(self._POST_PARAM_NAMES["descriptor_id"]) == None:
            return "Source-descriptor ID must be specified for copy."
        if postParams.get(self._POST_PARAM_NAMES["privacy_type"]) == None:
            return "Privacy type must be specified for copy."
        if postParams.get(self._POST_PARAM_NAMES["privacy_members"]) == None:
            return "Privacy members must be specified for copy."
        return None

    def react_to_threat_descriptor(
        self, descriptor_id, reaction, *, showURLs=False, dryRun=False
    ):
        """
        Does a POST to the reactions API.

        See: https://developers.facebook.com/docs/threat-exchange/reference/reacting
        """
        return self._postThreatDescriptor(
            "/".join(
                (
                    self._base_url,
                    str(descriptor_id),
                    f"?access_token={self.api_token}",
                )
            ),
            {"reactions": reaction},
            showURLs=showURLs,
            dryRun=dryRun,
        )

    def remove_reaction_from_threat_descriptor(
        self, descriptor_id, reaction, *, showURLs=False, dryRun=False
    ) -> t.List:
        """
        Does a POST to the reactions API.

        See: https://developers.facebook.com/docs/threat-exchange/reference/reacting
        """
        return self._postThreatDescriptor(
            "/".join(
                (
                    self._base_url,
                    str(descriptor_id),
                    f"?access_token={self.api_token}",
                )
            ),
            {"reactions_to_remove": reaction},
            showURLs=showURLs,
            dryRun=dryRun,
        )

    def upload_threat_descriptor(self, postParams, showURLs, dryRun):
        """
        Does a single POST to the threat_descriptors endpoint.  See also
        https://developers.facebook.com/docs/threat-exchange/reference/submitting
        """
        errorMessage = self._validate_post_params_for_submit(postParams)
        if errorMessage != None:
            return [errorMessage, None, None]

        url = "/".join(
            (self._base_url, "threat_descriptors", f"?access_token={self.api_token}")
        )

        return self._postThreatDescriptor(url, postParams, showURLs, dryRun)

    def copy_threat_descriptor(self, postParams, showURLs, dryRun):
        errorMessage = self._validate_post_pararms_for_copy(postParams)
        if errorMessage != None:
            return [errorMessage, None, None]

        # Get source descriptor
        sourceID = postParams["descriptor_id"]
        # Not valid for posting a new descriptor
        del postParams["descriptor_id"]
        sourceDescriptor = self.get_threat_descriptors([sourceID], showURLs=showURLs)
        sourceDescriptor = sourceDescriptor[0]

        # Mutate necessary fields
        newDescriptor = copy.deepcopy(sourceDescriptor)
        newDescriptor["indicator"] = sourceDescriptor["raw_indicator"]
        del newDescriptor["raw_indicator"]
        if "tags" in newDescriptor and newDescriptor["tags"] is None:
            del newDescriptor["tags"]

        # The shape is different between the copy-from data (mapping app IDs to
        # reactions) and the post data (just a comma-delimited string of owner-app
        # reactions).
        if "reactions" in newDescriptor:
            del newDescriptor["reactions"]

        # Take the source-descriptor values and overwrite any post-params fields
        # supplied by the caller. Note: Python's dict-update method keeps the old
        # value for a given field name when both old and new are present so we
        # invoke it seemingly 'backward'.
        #
        # Example:
        # * x = {'a': 1, 'b': 2, 'c': 3}
        # * y = {'a': 1, 'b': 9, 'd': 12}
        # * After y.update(x) then x is unchanged and y is
        #       {'a': 1, 'b': 2, 'd': 12, 'c': 3}
        #
        # This means we want newDescriptor.update(postParams)
        newDescriptor.update(postParams)

        # Get rid of fields like last_upated from the source descriptor which
        # aren't valid for post
        postParams = {}
        for key, value in newDescriptor.items():
            if self._POST_PARAM_NAMES.get(key) != None:
                postParams[key] = value

        return self.upload_threat_descriptor(postParams, showURLs, dryRun)

    def delete_threat_descriptor(
        self, descriptor_id, showURLs, dryRun
    ) -> t.List[t.Any]:
        url = (
            self._base_url
            + "/"
            + str(descriptor_id)
            + "?access_token="
            + self.api_token
        )
        if showURLs:
            print()
            print("(DELETE) URL:")
            print(url)
        if dryRun:
            print("Not doing DELETE since --dry-run.")
            return [None, None, ""]

        try:
            with self._get_session() as session:
                return [None, None, session.delete(url).json()]

        except urllib.error.HTTPError as e:
            responseBody = json.loads(e.read().decode("utf-8"))
            return [None, e, responseBody]

    def _postThreatDescriptor(self, url, postParams, showURLs, dryRun):
        """Code-reuse for submit and update"""
        for key, value in postParams.items():
            url += "&%s=%s" % (key, urllib.parse.quote(str(value)))
        if showURLs:
            print()
            print("(POST) URL:")
            print(url)
        if dryRun:
            print("Not doing POST since --dry-run.")
            return [None, None, ""]

        # Encode the inputs to the POST
        header = {"Content-Type": "text/json", "charset": "utf-8"}
        # This is a string
        data = urllib.parse.urlencode(postParams)
        # Turn it into a Python bytes object
        data = data.encode("ascii")

        # Do the POST
        try:
            with self._get_session() as session:
                return [None, None, session.post(url, data).json()]

        except urllib.error.HTTPError as e:
            responseBody = json.loads(e.read().decode("utf-8"))
            return [None, e, responseBody]

    def get_threat_descriptors_from_indicator(
        self, indicator_id: int, showURLs: bool = False
    ) -> t.List[t.Dict[str, t.Any]]:
        url = (
            self._base_url
            + "/"
            + str(indicator_id)
            + "?fields=descriptors&access_token="
            + self.api_token
        )

        if showURLs:
            print("url =", url)

        response = self.get_json_from_url(url)

        return response["descriptors"]["data"]
