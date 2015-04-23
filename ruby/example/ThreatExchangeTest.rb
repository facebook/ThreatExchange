#!/usr/bin/env ruby
# ThreatExchange example script.
require 'ThreatExchange'
require_relative 'lib/example'
access_token = 'abc123|somethingsomething'
TEClient = ThreatExchange::Client.new(access_token)
#------------------------------------------------------------------------------
banner('Example Malware Analysis')
query = {limit: 1000, text: 'bepush', strict_text: false}
spinner{ parse(TEClient.malware_analyses(query)) }
#------------------------------------------------------------------------------
banner('Example #2 Threat Exchange Members')
spinner{ parse(TEClient.members) }
#------------------------------------------------------------------------------
banner('Example #3 Threat Indicators')
query = {text: 'bepush', limit: 1000 }
spinner{ parse(TEClient.threat_indicators(query)) }
#------------------------------------------------------------------------------
banner('Example #4 Malware Objects')
query = {id: 518964484802467,
         fields: 'added_on,md5,sha1,sha256,status,victim_count,id'}
spinner{ parse(TEClient.indicator_pq(query)) }
#------------------------------------------------------------------------------
banner('Example #5 IOC Submission')
iocdata = {indicator: '63E070B2B434D07226C73A5773BFCC8D', type: 'HASH_MD5',
           description: 'API Test Ignore MD5sum of mcgrew',
           status: 'NON_MALICIOUS' }
spinner{ parse(TEClient.new_ioc(iocdata)) }
#------------------------------------------------------------------------------
banner('Example #6 IOC Update')
iocdata = {id: 735262776594935,
           description:"API Test, Ignore Update Test #{rand(9)}"}
spinner{ parse(TEClient.update_ioc(iocdata)) }
#------------------------------------------------------------------------------
banner('Example #7 IOC Update Valdiation')
query = {id: 735262776594935, fields: 'indicator,description,status,type'}
spinner{ parse(TEClient.indicator_pq(query)) }
#------------------------------------------------------------------------------
banner('Example #8 IOC Relation Generation')
iocdata = { id: 735262776594935, related_id: 823642271063499}
spinner{ parse(TEClient.new_relation(iocdata)) }
#------------------------------------------------------------------------------
banner('Example #9 IOC Relation Removal')
iocdata = { id: 735262776594935, related_id: 823642271063499}
spinner{ parse(TEClient.remove_relation(iocdata)) }