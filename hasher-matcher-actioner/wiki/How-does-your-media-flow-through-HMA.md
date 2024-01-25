Let's first show you the boundaries that HMA works within. Within your AWS account, you have many resources like S3 buckets, EC2 instances, lambda functions of your own. You spin up an instance of HMA inside this account. 

![Graphic showing HMA running within your cloud account](https://raw.githubusercontent.com/facebook/ThreatExchange/master/hasher-matcher-actioner/docs/images/HMA-Boundaries-Overview.png)

### Submitting content to HMA for flagging

Once it is up and running, you get an API you can submit your content to. HMA keeps itself up-to-date with ThreatExchange for the privacy groups or collaborations you have access to. Once a piece of content is submitted, HMA (still within your cloud provider account) compares that content to these ThreatExchange datasets and flags content that may be violating.

### Receiving flagged or potentially-violating content

There are two ways for your systems to receive flagged content from HMA.

1. You can configure a webhook 
2. You can call an API

We recommend the webhook. The webhook reduces latency. It is called as soon as the match is detected. While the API can only be polled. Excessive polling can be expensive because it hits the API resources frequently.

The webhook is an HTTP API call to a configurable URL within your systems. The payload contains information about the flagged content.