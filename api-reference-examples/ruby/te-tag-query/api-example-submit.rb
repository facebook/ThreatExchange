#!/usr/bin/env ruby

# ================================================================
# Copyright (c) Meta Platforms, Inc. and affiliates.
# ================================================================

require './TENet.rb'

ThreatExchange::TENet::setAppTokenFromEnvName('TX_ACCESS_TOKEN')

postParams = {
  'indicator' => 'dabbad00f00dfeed5ca1ab1ebeefca11ab1ec10e',
  'type' => 'HASH_SHA1',
  'description' => 'testing te-tag-query with post',
  'share_level' => 'AMBER',
  'status' => 'NON_MALICIOUS',
  'privacy_type' => 'HAS_WHITELIST',
  'privacy_members' => '1064060413755420', # This is the ID of another test app
  'tags' => 'testing_ruby_post',
}

showURLs = false
dryRun = false
validationErrorMessage, response_body, response_code = ThreatExchange::TENet::submitThreatDescriptor(
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
