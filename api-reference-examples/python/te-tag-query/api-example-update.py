#!/usr/bin/env python

# ================================================================
# Copyright (c) Meta Platforms, Inc. and affiliates.
# ================================================================

import sys
import json
import TE

TE.Net.setAppTokenFromEnvName("TX_ACCESS_TOKEN")

postParams = {
    "descriptor_id": "4036655176350945",  # ID of the descriptor to be updated
    "reactions": "INGESTED,IN_REVIEW",
}

showURLs = False
dryRun = False
validationErrorMessage, serverSideError, responseBody = TE.Net.updateThreatDescriptor(
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
