# Hasher Matcher Actioner Roadmap
This file gives some high level suggestions and ongoing direction for the Hasher Matcher Actioner (HMA) subproject in this repository, and larger projects that might need help to complete, if you are a developer interested in donating more time.
As of 9/2025, HMA has active interest, and some ongoing development. Some of these features might imply adding features to the underlying [python-threatexchange](https://github.com/facebook/ThreatExchange/tree/main/python-threatexchange) library, also hosted in this repository.

# Most Needed
These projects we think would most directly help with HMA in it's current state, either making it directly better for current adopters, or making it easier for new adopters to get started.

## Hardening Functionality for Production Deployment
HMA is built on flask and python, though the original authors don’t have much experience running this technology stack at scale. We’ve noticed some problems when trying to run the software at our targeted scale of ~10M hashes indexed, such as memory leaks (https://github.com/facebook/ThreatExchange/issues/1813).

The target scale for a multi-instance HMA deployment is to be able to support at least 10M indexed hashes with 4k lookups per second, and for potential adopters to be able to test the technology with sampled traffic with only a single machine. Making sure there are ways to manage such a deployment in production compatible with a few different infrastructure choices is our top priority.

## Functionality for Confirming/Deconfirming Signals from Exchanges
One of the key features of HMA is the integration with Exchanges, which allow receiving hashes from third parties. Sometimes, despite the best practices of all contributors to an exchange, it may turn out that a benign image that only exists on your platform will show as matching to one of these hashes. Even a single signal can unexpectedly create a flood of matches that might otherwise overwhelm your downstream review queue.

There are a suite of features that are needed to defend against this, but having them can improve the baseline capabilities of HMA as whole:
1. **Configurable match distance**: PDQ for example supports matching things from distance 0-31 by default. You can reduce the distance in order to increase match precision, at the expense of recall, which may make sense for some platforms.
1. **Negative Banks**: These banks instead suppress match events of specific other banks. Which banks suppress should be configurable as part of the original bank’s configuration.
1. **Flood prevention & Review**: Approximate match counts for individual hash ids can be maintained in memory, and if the number of matches exceeds an expected baseline, the signal can be quarantined, preventing match events, and potentially logging to a separate location.
1. **Confirming / Deconfirming Third Party Signals**: For banks that are from third parties, once you have manually reviewed a match and confirm it matches what you expect, you can move the signal to a “confirmed” bank, or otherwise treat it differently. We should provide an API that allows recording a piece of content was harmful even if we are not banking it, and recording that the signal(s) that led to that match were valuable. Signals that don’t match harmful content could also have their matching disabled temporarily or permanently. 

## Improving Explainability and Demo Features
HMA is meant to be an introduction to photo/video similarity hashing, and tools to help debug why things are matching or not matching are key for earlier experiences. A UI-centric experience for re-running a previous matches, debugging why something does or does not match is key to gaining confidence in the system.

Additionally, displaying more metadata about test matches, especially information from an exchange could help gain confidence in matches that are happening. 

# Areas of Exploration for Expanding HMA Capabilities
Content moderation is a very big place, and HMA is a narrow tool for a certain type of detection. These are projects demonstrate new ways HMA can be useful, or add functionality that helps improve the wider ecosystem.

## Recently Seen Content Clustering & Retroactive Matching
It is possible to insert every item that is passed into HMA into its own index, which can be used to automatically cluster similar images. This can be useful for understanding content on a platform, but also allows you to match content uploaded before you learn a piece of content is of interest. 

A ring buffer of in-memory indices with a UI page and API for querying previously uploaded content can provide a demonstrator, and unlock additional functionality.

## Functionality for Sharing Match and Feedback with an Exchange
If Confirming/Deconfirming is implemented, then having a table for your instance’s feedback to the exchange, and allowing to sync that feedback via the exchanges API can provide value to the participants of the exchange. This will likely require adding feedback to the Exchange interface in python-threatexchange.

## Functionality for Sharing the Content of a Bank with an Exchange
Many exchanges provide both read and write functionality, but only read behavior (i.e. copying the exchange into a local bank), is implemented. A symmetrical implementation that allows copying data out of a bank and maintaining it in the exchange would also be of interest, but similar to match and feedback would require changes to the exchange interface in python-threatexchange.
