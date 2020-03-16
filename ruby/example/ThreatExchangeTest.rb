#!/usr/bin/env ruby
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
# ThreatExchange example script.
require 'ThreatExchange'
require_relative 'lib/example'

appid = 'abc'
secret = 'def'
TEClient = ThreatExchange::Client.new(appid, secret)
RestClient.log = Logger.new(STDOUT) if ENV['WITH_LOGGING'] == '1'

indicator_id = '63E070B2B434D07226C73A5773BFCC8D'
new_descriptor_id = nil


banner('Example: Threat Privacy Groups (Owned)')
query = {}
spinner{ parse(TEClient.owned_threat_privacy_groups(query) )}
#------------------------------------------------------------------------------
banner('Example: Threat Privacy Groups (Member)')
query = {}
spinner{ parse(TEClient.member_threat_privacy_groups(query) )}
#------------------------------------------------------------------------------
# WARNING this example actually creates a privacy group
# banner('Example: Create a Threat Privacy Group')
# query = {name: 'API_Test', description: 'API test of privacy group creation'}
# spinner{ parse(TEClient.new_threat_privacy_group(query)) }
#------------------------------------------------------------------------------
banner('Example: List TE Members')
spinner{ parse(TEClient.members['data'].map { |m| m['name'] }) }
#------------------------------------------------------------------------------
banner('Example: Malware Families')
query = {text: 'bepush', strict_text: false, limit: 3}
spinner{ parse(TEClient.malware_families(query)) }
#------------------------------------------------------------------------------
banner('Example: Malware Analysis')
query = {text: 'bepush', strict_text: false, limit: 3}
spinner{ parse(TEClient.malware_analyses(query)) }
#------------------------------------------------------------------------------
banner('Example: List Threat Descriptors')
query = {text: 'bepush', limit: 3}
spinner{ parse(TEClient.threat_descriptors(query)) }
#------------------------------------------------------------------------------
banner('Example: Search Threat Indicators')
query = {text: 'bepush', limit: 3}
spinner{ parse(TEClient.threat_indicators(query)) }
#------------------------------------------------------------------------------
banner('Example: New Descriptor')
query = {
  description: 'API Test Ignore MD5sum of mcgrew',
  indicator: indicator_id,
  privacy_type: 'VISIBLE',
  share_level: 'WHITE',
  status: 'NON_MALICIOUS',
  type: 'HASH_MD5'
}
spinner{ new_descriptor_id = parse(TEClient.new_descriptor(query))['id'] }
#------------------------------------------------------------------------------
banner('Example: Update Indicator')
query = {
  id: new_descriptor_id,
  description:"API Test, Ignore Update Test #{rand(9)}"
}
spinner{ parse(TEClient.update_indicator(query)) }
#------------------------------------------------------------------------------
banner('Example: Get Indicator')
query = {id: new_descriptor_id, fields: 'indicator,description,status,type'}
spinner{ parse(TEClient.get_indicator(query)) }
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
banner('Example: New Indicator Relation')
query = { id: 735262776594935, related_id: 823642271063499}
spinner{ parse(TEClient.new_relation(query)) }
#------------------------------------------------------------------------------
banner('Example: Delete Indicator Relation')
query = { id: 735262776594935, related_id: 823642271063499}
spinner{ parse(TEClient.remove_relation(query)) }
#------------------------------------------------------------------------------

