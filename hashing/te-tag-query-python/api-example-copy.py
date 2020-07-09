##!/usr/bin/env python

# ================================================================
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
# ================================================================

import sys
import json
import TE

TE.Net.setAppTokenFromEnvName('TX_ACCESS_TOKEN')

postParams = {
  'descriptor_id': '4036655176350945',
  'indicator': 'dabbad00f00dfeed5ca1ab1ebeefca11ab1ec21b',
  'privacy_type': 'HAS_PRIVACY_GROUP',
  'privacy_members': '781588512307315',
}

showURLs = True
dryRun = False
validationErrorMessage, serverSideError, responseBody = TE.Net.copyThreatDescriptor(
  postParams, showURLs, dryRun)

if validationErrorMessage != None:
  sys.stderr.write(validationErrorMessage + "\n")
  sys.exit(1)

if serverSideError != None:
  sys.stderr.write(str(serverSideError) + "\n")
  sys.stderr.write(json.dumps(responseBody) + "\n")
  sys.exit(1)

print(json.dumps(responseBody))
