#!/usr/bin/env python

# ================================================================
# Copyright (c) Meta Platforms, Inc. and affiliates.
# ================================================================

import sys
import json
import TE

TE.Net.setAppTokenFromEnvName("TX_ACCESS_TOKEN")

postParams = {
    # ID of descriptor to make a copy of. All remaining fields are overrides to
    # that copy-from template.
    "descriptor_id": "4036655176350945",
    "indicator": "dabbad00f00dfeed5ca1ab1ebeefca11ab1ec21b",
    # This is the ID of a privacy group which includes two test apps.
    #
    # See also
    # https://developers.facebook.com/apps/your-app-id-goes-here/threat-exchange/privacy_groups
    #
    # Note: in the TEAPI at present we can't read the privacy-members of a
    # copy-from descriptor unless we already own it, so this needs to be
    # specified explicitly here.
    "privacy_type": "HAS_PRIVACY_GROUP",
    "privacy_members": "781588512307315",  # Comma-delimited if there are multiples
}

showURLs = True
dryRun = False
validationErrorMessage, serverSideError, responseBody = TE.Net.copyThreatDescriptor(
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
