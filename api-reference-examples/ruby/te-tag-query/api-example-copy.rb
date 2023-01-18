#!/usr/bin/env ruby

# ================================================================
# Copyright (c) Meta Platforms, Inc. and affiliates.
# ================================================================

require './TENet.rb'

ThreatExchange::TENet::setAppTokenFromEnvName('TX_ACCESS_TOKEN')

postParams = {
  # ID of descriptor to make a copy of. All remaining fields are overrides to
  # that copy-from template.
  'descriptor_id' => '4036655176350945',

  # This is the ID of a privacy group which includes two test apps.
  #
  # See also
  # https://developers.facebook.com/apps/your-app-id-goes-here/threat-exchange/privacy_groups
  #
  # Note: in the TEAPI at present we can't read the privacy-members of a
  # copy-from descriptor unless we already own it, so this needs to be
  # specified explicitly here.
  'indicator' => 'dabbad00f00dfeed5ca1ab1ebeefca11ab1ec21b',
  'privacy_type' => 'HAS_PRIVACY_GROUP',
  'privacy_members' => '781588512307315', # Comma-delimited if there are multiples
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
