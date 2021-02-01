# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
This is an entire copy of a file from ThreatExchange/hashing

TODO: Slim down to only what we need
"""

import copy
import datetime
import json

# General Python dependencies
import os
import re
import urllib.parse

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


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


DEFAULT_TE_BASE_URL = "https://graph.facebook.com/v6.0"
_retry_strategy = Retry(
    total=4,
    status_forcelist=[429, 500, 502, 503, 504],
    method_whitelist=["HEAD", "GET", "OPTIONS"],
)


def get_fb_graph_api():
    """
    Custom requests session that provides
    - retries: retries on GET requests for 429 or 5XX error codes
    - timeout: timeout slow requests. Can be adjusted at the
               fb_graph_api.get(.., timeout=FOO) level

    Ideally, should be used within a context manager:
    ```
    with get_fb_graph_api() as fb_graph_api:
        fb_graph_api.get()...
    ```

    If using without a context manager, ensure you end up calling close() on
    the returned value.

    TODO: Identify if requests Session object can be used across threads in a
    `concurrent.futures.ThreadPoolExecutor`
    Filed:  https://github.com/facebook/ThreatExchange/issues/348
    - because a session is created per call to get_fb_graph_api(), the
      underlying conn pool can't be used.
    - this might become a performance concern if the pre-flight latencies
      become significant because we make many small requests and not few large
      ones.
    - right now, choosing to go ahead with one session per call as is typical
      in requests.get() equivalents
    """
    session = requests.Session()
    session.mount(
        DEFAULT_TE_BASE_URL,
        adapter=TimeoutHTTPAdapter(timeout=60, max_retries=_retry_strategy),
    )
    return session


class Net:
    THREAT_DESCRIPTOR = "THREAT_DESCRIPTOR"
    TE_BASE_URL = DEFAULT_TE_BASE_URL
    APP_TOKEN = None

    # This is just a keystroke-saver / error-avoider for passing around
    # post-parameter field names.

    POST_PARAM_NAMES = {
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

    @classmethod
    def getJSONFromURL(self, url):
        """
        Perform an HTTP GET request, and return the JSON response payload.
        Same timeouts and retry strategy as `fb_graph_api` above.
        """
        with get_fb_graph_api() as api:
            return api.get(url).json()

    # ----------------------------------------------------------------
    # Looks up the "objective tag" ID for a given tag. This is suitable input for the /threat_tags endpoint.

    @classmethod
    def getTagIDFromName(self, tagName, showURLs=False):
        url = (
            self.TE_BASE_URL
            + "/threat_tags"
            + "/?access_token="
            + self.APP_TOKEN
            + "&text="
            + urllib.parse.quote(tagName)
        )
        if showURLs:
            print("URL:")
            print(url)

        response = self.getJSONFromURL(url)

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

    # ----------------------------------------------------------------
    # Looks up all metadata for given IDs.
    @classmethod
    def getInfoForIDs(self, ids, **kwargs):
        verbose = kwargs.get("verbose", False)
        showURLs = kwargs.get("showURLs", False)
        includeIndicatorInOutput = kwargs.get("includeIndicatorInOutput", True)

        # Check well-formattedness of descriptor IDs (which may have come from
        # arbitrary data on stdin).
        for id in ids:
            try:
                _ = int(id)
            except ValueError:
                raise Exception('Malformed descriptor ID "%s"' % id)

        # See also
        # https://developers.facebook.com/docs/threat-exchange/reference/apis/threat-descriptor/v6.0
        # for available fields

        url = (
            self.TE_BASE_URL
            + "/?access_token="
            + self.APP_TOKEN
            + "&ids="
            + ",".join(ids)
            + "&fields=raw_indicator,type,added_on,last_updated,confidence,owner,privacy_type,review_status,status,severity,share_level,tags,description,reactions,my_reactions"
        )

        if showURLs:
            print("URL:")
            print(url)

        response = self.getJSONFromURL(url)

        descriptors = []
        for id, descriptor in response.items():
            if includeIndicatorInOutput == False:
                del descriptor["raw_indicator"]
            if verbose:
                print(json.dumps(descriptor))

            tags = descriptor.get("tags", None)
            if tags is None:
                tags = []
            else:
                tags = tags["data"]

            # Canonicalize the tag ordering and simplify the
            # structure to simply an array of tag-texts
            descriptor["tags"] = sorted(tag["text"] for tag in tags)

            if descriptor.get("description") is None:
                descriptor["description"] = ""

            descriptors.append(descriptor)

        return descriptors

    # ----------------------------------------------------------------
    # Gets threat updates for the given privacy group.
    @classmethod
    def getThreatUpdates(self, privacy_group, next_page=None, **kwargs):
        if next_page is not None:
            url = next_page
        else:
            url = (
                self.TE_BASE_URL
                + "/"
                + str(privacy_group)
                + "/threat_updates/"
                + "?access_token="
                + self.APP_TOKEN
                + "&fields=id,indicator,type,creation_time,last_updated,should_delete,tags,status,applications_with_opinions"
            )
            for arg, value in kwargs.items():
                if value is not None:
                    if arg == "types":
                        url += "&types=" + ",".join(value)
                    else:
                        url += "&" + arg + "=" + str(value)
        return self.getJSONFromURL(url)

    # ----------------------------------------------------------------
    # Returns error message or None.
    # This simply checks to see (client-side) if required fields aren't provided.
    @classmethod
    def validatePostPararmsForSubmit(self, postParams):
        if postParams.get(self.POST_PARAM_NAMES["descriptor_id"]) != None:
            return "descriptor_id must not be specified for submit."

        requiredFields = [
            self.POST_PARAM_NAMES["indicator"],
            self.POST_PARAM_NAMES["type"],
            self.POST_PARAM_NAMES["description"],
            self.POST_PARAM_NAMES["share_level"],
            self.POST_PARAM_NAMES["status"],
            self.POST_PARAM_NAMES["privacy_type"],
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

    # ----------------------------------------------------------------
    # Returns error message or None.
    # This simply checks to see (client-side) if required fields aren't provided.
    @classmethod
    def validatePostPararmsForCopy(self, postParams):
        if postParams.get(self.POST_PARAM_NAMES["descriptor_id"]) == None:
            return "Source-descriptor ID must be specified for copy."
        if postParams.get(self.POST_PARAM_NAMES["privacy_type"]) == None:
            return "Privacy type must be specified for copy."
        if postParams.get(self.POST_PARAM_NAMES["privacy_members"]) == None:
            return "Privacy members must be specified for copy."
        return None

    @classmethod
    def reactToThreatDescriptor(
        cls, descriptor_id, reaction, *, showURLs=False, dryRun=False
    ):
        """
        Does a POST to the reactions API.

        See: https://developers.facebook.com/docs/threat-exchange/reference/reacting
        """
        return cls._postThreatDescriptor(
            "/".join(
                (cls.TE_BASE_URL, str(descriptor_id), f"?access_token={cls.APP_TOKEN}")
            ),
            {"reactions": reaction},
            showURLs=showURLs,
            dryRun=dryRun,
        )

    # ----------------------------------------------------------------
    # Does a single POST to the threat_descriptors endpoint.  See also
    # https://developers.facebook.com/docs/threat-exchange/reference/submitting
    @classmethod
    def submitThreatDescriptor(self, postParams, showURLs, dryRun):
        errorMessage = self.validatePostPararmsForSubmit(postParams)
        if errorMessage != None:
            return [errorMessage, None, None]

        url = (
            self.TE_BASE_URL
            + "/threat_descriptors"
            + "/?access_token="
            + self.APP_TOKEN
        )

        return self._postThreatDescriptor(url, postParams, showURLs, dryRun)

    @classmethod
    def copyThreatDescriptor(self, postParams, showURLs, dryRun):
        errorMessage = self.validatePostPararmsForCopy(postParams)
        if errorMessage != None:
            return [errorMessage, None, None]

        # Get source descriptor
        sourceID = postParams["descriptor_id"]
        # Not valid for posting a new descriptor
        del postParams["descriptor_id"]
        sourceDescriptor = self.getInfoForIDs([sourceID], showURLs=showURLs)
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
            if self.POST_PARAM_NAMES.get(key) != None:
                postParams[key] = value

        return self.submitThreatDescriptor(postParams, showURLs, dryRun)

    # ----------------------------------------------------------------
    # Code-reuse for submit and update
    @classmethod
    def _postThreatDescriptor(self, url, postParams, showURLs, dryRun):
        for key, value in postParams.items():
            url += "&%s=%s" % (key, urllib.parse.quote(str(value)))
        if showURLs:
            print()
            print("URL:")
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
            with get_fb_graph_api() as fb_graph_api:
                return [None, None, fb_graph_api.post(url, data).json()]

        except urllib.error.HTTPError as e:
            responseBody = json.loads(e.read().decode("utf-8"))
            return [None, e, responseBody]
