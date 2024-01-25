# HMA at a glance

HMA was developed to help you keep your online community safe. It makes it easy for you get started on common trust-and-safety / content integrity workflows. Here's a super-quick walk-through of the HMA system.

![Graphic showing HMA running within your cloud account](https://raw.githubusercontent.com/facebook/ThreatExchange/master/hasher-matcher-actioner/docs/images/HMA-Boundaries-Overview.png)

HMA is ready-to-deploy to your AWS account. Your user's content is private. It does not leave your AWS account.

## Pull and synchronize datasets from ThreatExchange
[ThreatExchange](https://developers.facebook.com/docs/threat-exchange/) is a platform where participating organizations share [Signals](Glossary#hasher) of potentially violating [Content](Glossary#hasher) using a convenient, structured, and easy-to-use API that provides privacy controls to enable sharing with only desired groups.

The HMA system automatically pulls in data for [PrivacyGroups](Glossary#fetcher) you are a member of and keeps it up to date.

## Process images and find matches in datasets

[Use the Content Submission API](Tutorial:-Programmatically-Submitting-Photos-to-HMA) or point HMA to an S3 bucket to have HMA take a look at them and see if they have been flagged by any of the [Datasets](Glossary#matcher) pulled for your PrivacyGroup(s).

## Integrate with your systems

You can configure HMA to call a [Webhook](Glossary#actioner) in your system if a [Match](Glossary#matcher) is found. You can fine-tune the rules so that only those Photos that match specific PrivacyGroups or have been [Classified](Glossary#matcher) in a specific way trigger the Webhook call.

## Contribute back and reduce online harm

If you spend some time doing human review on Content that has been flagged by HMA, you can send your [Opinion](Glossary#writebacker) back to ThreatExchange. Using this feature, you can automatically take an [Action](Glossary#actioner) (call another webhook) on Content that you have previously reviewed.

## Performance and Scalability

HMA has been tested at 2000 images per second. The performance is a function of provisioned capacity on your AWS account resources. HMA can perform at higher scales if provided `AWS Lambda Concurrency` and `AWS DynamoDB Write Units`.

----

Take the next step: deploy the HMA system into your AWS account! It barely takes a minute!