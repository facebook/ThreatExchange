# This file should contain all the record creation needed to seed the database with its default values.
# The data can then be loaded with the rake db:seed (or created alongside the db with db:setup).
#
# Examples:
#
#   cities = City.create([{ name: 'Chicago' }, { name: 'Copenhagen' }])
#   Mayor.create(name: 'Emanuel', city: cities.first)
indicator_types = IndicatorType.create([{ name: 'DOMAIN'}, { name: 'EMAIL_ADDRESS'}, { name: 'HASH_MD5'}, { name: 'IP_ADDRESS'}, { name: 'REGISTRY_KEY'}, { name: 'USER_AGENT'}])
threat_types = ThreatType.create([{ name: 'BAD_ACTOR'}, { name: 'COMPROMISED_CREDENTIAL'}, { name: 'MALICIOUS_AD'}, { name: 'MALICIOUS_DOMAIN'}, { name: 'MALICIOUS_IP'}, { name: 'MALICIOUS_URL'}, { name: 'MALWARE_ARTIFACTS'}, { name: 'MALWARE_SAMPLE'}, { name: 'PROXY_IP'}, { name: 'UNKNOWN'}])
status_types = Status.create([{ name: 'UNKNOWN'}, { name: 'SUSPICIOUS'}, { name: 'MALICIOUS'}, { name: 'NON_MALICIOUS'}])
severity_types = SeverityType.create([{ name: 'INFO'}, { name: 'WARNING'}, { name: 'UNKNOWN'}, { name: 'SUSPICIOUS'}, { name: 'SEVERE'}, { name: 'APOCALYPSE'}])
privacy_types = PrivacyType.create([{ name: 'VISIBLE'}, { name: 'NONE'}])
share_level_types = ShareLevelType.create([{ name: 'RED'}, { name: 'AMBER'}, { name: 'GREEN'}, { name: 'WHITE'}])
