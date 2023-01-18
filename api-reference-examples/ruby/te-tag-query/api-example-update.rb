#!/usr/bin/env ruby

# ================================================================
# Copyright (c) Meta Platforms, Inc. and affiliates.
# ================================================================

require './TENet.rb'

ThreatExchange::TENet::setAppTokenFromEnvName('TX_ACCESS_TOKEN')
postParams = {
  'descriptor_id' => '3546989395318416', # ID of the descriptor to be updated
  'reactions': 'INGESTED,IN_REVIEW'
}

showURLs = false
dryRun = false
validationErrorMessage, response_body, response_code = ThreatExchange::TENet::updateThreatDescriptor(
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
