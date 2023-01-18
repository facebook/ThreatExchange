#!/usr/bin/env python

# ================================================================
# Copyright (c) Meta Platforms, Inc. and affiliates.
# ================================================================

import sys
import json
import TE

TE.Net.setAppTokenFromEnvName("TX_ACCESS_TOKEN")

postParams = {
    "indicator": "dabbad00f00dfeed5ca1ab1ebeefca11ab1ec20f",
    "type": "HASH_SHA1",
    "description": "testing API-example post",
    "share_level": "AMBER",
    "status": "NON_MALICIOUS",
    "privacy_type": "HAS_WHITELIST",
    "privacy_members": "1064060413755420",  # This is the ID of another test app
    "tags": "testing_python_post",
}

showURLs = False
dryRun = False
validationErrorMessage, serverSideError, responseBody = TE.Net.submitThreatDescriptor(
    postParams, showURLs, dryRun
)

if validationErrorMessage != None:
    sys.stderr.write(validationErrorMessage + "\n")
    sys.exit(1)

if serverSideError != None:
    sys.stderr.write(str(serverSideError) + "\n")
    sys.stderr.write(json.dumps(responseBody) + "\n")
    sys.exit(1)

print(json.dumps(responseBody))
