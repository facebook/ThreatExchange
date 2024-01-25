# Terms and concepts used in HMA

_**Hasher-Matcher-Actioner**_ (aka HMA) : An open-source integrity tool which a Platform can deploy to address Content Moderation problems

_**Platform**_ : An social network with a community of users who can upload Content

## HMA Components
- _**Hasher**_ : The component of HMA that converts Content in to Signals. Currently, the hasher can only accept a single ContentType (Photos) and can only produce a single SignalType (PDQ Hash)
- _**Matcher**_ : The component of HMA that determines which Datasets a Signal is present in, creating Matches connecting those Datasets to the relevant piece of Content. A Signal can Match mutiple times against the same Dataset. For example, HMA might have two Datasets, one for cats and one for dogs. When Content is passed to the Hasher, a new Signal is produced. That Signal might be present in none, one, or both of those Datasets creating zero, one, two, or more Matches.
- _**Actioner**_ : The component of HMA that notifies an external system when a Match is created. This is primarily used to communicate with the Platform that deployed HMA. Note that there is a different component, Writebacker, that is used to notify Sources of Matches and other events
- _**Fetcher**_ : The component of HMA that reads Signals and Opinions from Sources to build Datasets and keep them in sync.
- _**Writebacker**_ : The component of HMA that sends Opinions, Matches, and new Signals back to the Sources.

## Core Terms for each Component
### Hasher
   - _**Content**_ : An item generate by a user of the Platform, which should be checked against the Community Standards of the Platform. Content might itself be composed of multiple pieces of Content (a photo with a caption, a video that has a thumbnail, etc.)
   - _**ContentType**_ : A category of Content which has a specific set of SignalTypes that can be generated from it (by the Hasher) and  compared against (by the Matcher). For example, Photo is a ContentType which can generate various SignalTypes such as PDQ, PDQ+OCR, or PhotoMD5. Currently, "Photo" is the only ContentType supported by HMA though there are future development plans to support Video, Text, and URLs.
   - _**Signal**_ : An input to a MatchingAlgorithm that can be used to identify Content
   - _**SignalType**_ : A category of Signals that are derived from Content in the same way and can be compared against other Signals of the same SignalType via a MatchingAlgorithm
   - _**HashingAlgorithm**_ : An algorithm that can take a photo or Video Content and create a Signal from it. Read more [here](https://en.wikipedia.org/wiki/Perceptual_hashing)
   - _**Hash**_ : The output of a HashingAlgorithm. Hashes are a subset of Signals

### Matcher
   - _**Dataset**_ : A collection of Signals who's Content is purportedly all related. For example, HMA may contain a cat Dataset of PDQ Hashes of cat Photos.
   - _**MatchingAlgorithm**_ : An algorithm that can take a Signal and a Dataset and determine if the Signal is present in the Dataset.
   - _**Match**_ : The output of a MatchingAlgorithm. If a Match is created because a Signal was present in a Dataset, it _usually_ implies that the Content from which the Signal was derived fits the purpose of the Dataset. In our example from the Matcher definition above, a Match would imply the Content is _probably_ a picture of a cat.
   - _**MatchedSignal**_ : The Signal in a Dataset which a piece of Content Matches
   - _**Classification (aka Label)**_ : A piece of metadata about a Match such as the Dataset the MatchedSignal is in, the ID of the MatchedSignal, or the  Signal. These Classifications are used by the Actioner to determine which Actions should be run based on a Match. Read more about how the Actioner uses Classifications [here](Action-Rule-Evaluation).

### Actioner
   - _**Action**_ : A method for notifying a system outside of HMA, usually the Platform, that a Match has occurred. For example, if we have a Dataset of cat Photos, after a piece of Content matches the Dataset, the Platform should be notified so that it can review the Content and, if it is truly a cat, remove it for violating the Platform's Community Standards. HMA currently supports only a single notification framework, Webhooks. Read more about configuring Actions in HMA [here](https://github.com/facebook/ThreatExchange/wiki/Tutorial:-How-to-Notify-My-System-when-My-Content-Matches-a-Dataset).
   - _**Webhook**_ : A configurable [HTTP request](https://en.wikipedia.org/wiki/Hypertext_Transfer_Protocol) sent to a Platform's system that contains a JSON object describing the Match for the Platform to process. HMA allows you to configure when Webhooks are sent, what URL address they are sent to, and with what parameters. Read more about Webhooks as a concept [here](https://sendgrid.com/blog/whats-webhook/). Read more about configuring Webhook Actions in HMA [here](https://github.com/facebook/ThreatExchange/wiki/Tutorial:-How-to-Notify-My-System-when-My-Content-Matches-a-Dataset).
   - _**ActionRule**_ : A configurable algorithm which takes a Match and determine what Actions, if any, should be performed as a result. Read more about configuring ActionRules in HMA [here](Action-Rule-Evaluation).

### Fetcher
   - _**Source**_ : An externally hosted API that can provide Datasets. Through the Fetcher, HMA builds and maintains Datasets through that API. Some Sources also host Opinions and Matches as well. Sources have mechanisms for Contributing Signals or for providing Opinions of Signals. The Writebacker handles sharing Signals, Opinions, and Matches with Sources. HMA currently supports two Sources: ThreatExchange and LocalDatasets.
   - _**ThreatExchange**_: A Source API hosted by Facebook for sharing Datasets and collaborating amongst Platforms. Read more and learn how to get access the ThreatExchange [here](https://developers.facebook.com/docs/threat-exchange/getting-started)
   - _**PrivacyGroup (aka Collaboration)**_ : The ThreatExchange-specific term for a Dataset. PrivacyGroups also contain the concept of privacy which controls who has access to the Dataset. This enables you to contribute Signals and Opinions with specific Platforms rather than all Platforms on ThreatExchange. Read more [here](https://developers.facebook.com/docs/threat-exchange/reference/apis/threat-privacy-group/)
   - _**Application**_ : The ThreatExchange-specific term for a Platform. This is used to specify the privacy of Signals shared via ThreatExchange
   - _**Indicator**_ : The ThreatExchange-specific term for Content.
   - _**Tag**_ : The ThreatExchange-specific term for Classification.
   - _**LocalDatasets**_ : HMA can be used as a standalone integrity product without access to ThreatExchange or any other Source. To use HMA without other Sources you will need to provide your own Datasets. See how [here](https://github.com/facebook/ThreatExchange/wiki/Tutorial:-Uploading-Datasets-to-HMA)

### Writebacker
   - _**Opinion**_ : A subjective decision made by a Platform about Match. Currently, HMA supports two Opinions: TruePositive or FalsePositive
   - **_TruePositive_** : A TruePositive Opinion indicates that the Platform believes that the Signal rightfully belongs to the Dataset it has matched to. In our cat example from the Matcher definition above, after a Match has occurred, if the Platform reviews the Content and agrees the Content is an Photo of a cat, they should add the TruePositive Opinion to the Match.
   - **_FalsePositive_** : A FalsePositive Opinion indicates that the Platform believes that the Signal should not be in the Dataset it has matched to. In our cat example from the Matcher definition above, after a Match has occurred, if the Platform reviews the Content and believes the Content is not an Photo of a cat, they should add the FalsePositive Opinion to the Match.
   - _**Contribute**_ : Contributing is when a Platform elects to share its Signals, Opinions, or Matches with another Platform. Contributing allows Platforms to collaborate to solve common problems across the internet. It also allows Platforms to learn the value the Signals they share are providing to other Platforms. HMA makes contributing as easy as flipping a switch. [Look here to see how](https://github.com/facebook/ThreatExchange/wiki/How-to-disable-writebacks-to-ThreatExchange)


## Other Terminology used in Content Moderation
- _**Community Standards**_: A Platform's rules for what Content can be on its site. Content that breaks the rules may be actioned (ex: deleted), potentially leading to even the user being actioned (ban).
- _**ViolationType**_ : A reasoning for a decision made on a pieces of Content that maps to a section of a Partner's Community Standards.