##!/usr/bin/env ruby

# ================================================================
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
# ================================================================

require './TENet.rb'

ThreatExchange::TENet::setAppTokenFromEnvName('TX_ACCESS_TOKEN')

postParams = {
  'descriptor_id' => '4036655176350945',
  'indicator' => 'dabbad00f00dfeed5ca1ab1ebeefca11ab1ec21b',
  'privacy_type' => 'HAS_PRIVACY_GROUP',
  'privacy_members' => '781588512307315',
}

showURLs = false
dryRun = false
validationErrorMessage, response_body, response_code = ThreatExchange::TENet::copyThreatDescriptor(
  postParams,
  showURLs: showURLs,
  dryRun: dryRun)

unless validationErrorMessage.nil?
  $stderr.puts validationErrorMessage
  exit 1
end

puts response_body

if response_code != 200
  exit 1
end
