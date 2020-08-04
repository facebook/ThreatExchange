# ThreatExchange Webhooks Subscription

An external server that will be notified whenever a threat descriptor, malware family, or malware analysis is updated or created.

# Steps
1. Create a FB app and register it with ThreatExchange.
2. Set up an external server such as Heroku using this code. For refence, view the documentation [here](https://developers.facebook.com/docs/threat-exchange/webhooks#callback).
3. Enable Webhooks in your ThreatExchange Developer's app, subscribe to 'threat_descriptor', 'malware_analysis', or 'malware_families"  via the Webhooks Graph API under 'Threat Exchange', and set your server website as the callback URL with /get_updates.php ammended. For the "Verify Token", use any non-empty string. For more details on this process, view the [Enabling Webhooks](https://developers.facebook.com/docs/threat-exchange/webhooks#enable) documentation. 
