The [Actioner](Glossary#actioner) component of HMA controls how external systems are notified when a [Match](Glossary#matcher) is created. This is primarily used to communicate with the [Platform](Glossary#terms-and-concepts-used-in-hma) that deployed HMA. This document describes how the Actioner makes decisions about who to notify and how it notifies them. 

The decision layer of the Actioner is the [ActionRules](Glossary#actioner) framework. You can think of an ActionRule as an algorithm that takes in a Match as input and outputs either a specific Action on no action. When a Match is created, it has various [Classifications](Glossary#matcher) (sometimes also called Labels) which describe the Match such as where the [Content](Glossary#hasher) came from, what [Dataset](Glossary#matcher) it matched against, where that Dataset originated, and more. The ActionRules framework reads these Classifications and determines which Actions should be run.

Actions, in turn, specify how to notify the external system (like your Platform). Currently, there is only one method of notifying an external system, [Webhooks](Webhooks-Reference). Read about how to set up Webhooks [here](https://github.com/facebook/ThreatExchange/wiki/Tutorial:-How-to-Notify-My-System-when-My-Content-Matches-a-Dataset).

Let's look at an example where you have 2 Datasets, one for Cats and one for Dogs. Your Platform has 3 systems for enforcing your [Community Standards](Glossary#other-terminology-used-in-content-moderation): High Severity (HS), Low Severity (LS), and Record Keeping (RK). On your Platform, cat images are a high severity violation and so cat images must be sent to the HS system. Dog images, however, are a Low severity violation and can be handled by the LS system. For both cat and dog matches, we want to notify our Record Keeping system, RK.  

For each system, you'll need to create an Action which communicate with that system. This is done via Webhooks and you can find the details [here](Webhooks-Reference). We then need to set up a series of ActionRules for our logic. Specifically, we need 4 rules.

Here you can see how our 4 ActionRules and 3 Actions would work to notify HighSeverity and RecordKeeping systems of a cat Match:
![](https://github.com/facebook/ThreatExchange/blob/main/hasher-matcher-actioner/docs/images/ActionRule%20Cat%20Match%20Example.png)

Here you can see how our 4 ActionRules and 3 Actions would work to notify LowSeverity and RecordKeeping systems of a dog Match:
![](https://github.com/facebook/ThreatExchange/blob/main/hasher-matcher-actioner/docs/images/ActionRule%20Dog%20Match%20Example.png)

## How to specify ActionRules
ActionRules can be created and modified on the [ActionRules tab of the Settings page](The-Action-Rules-Page). [This tutorial](https://github.com/facebook/ThreatExchange/wiki/Tutorial:-How-to-Notify-My-System-when-My-Content-Matches-a-Dataset#step-3---create-actionrule-to-trigger-your-action-when-a-match-occurs) explains how to use the page to define ActionRules.

Returning to our example, for an ActionRule like "Notify HS system if Cat" we'd specify it as follows:
- **Name** : `Notify HS System If Cat`
    - A unique name for the ActionRule
- **Classifications** : `DatasetID = 12345`
    - This field allows you to specify the logic of the ActionRules in terms of what must be present or not present on the Match in order to trigger the specified Action. If our cat [Dataset](Glossary#matcher) has id `12345`, we should specify all that DatasetID must equal "12345" to guarantee that all matches to the cat Dataset trigger the specified Action. See below for list of available Classifications
- **Action** : `Notify HighSeverity`
    - This field specifies which action should be called. The options here are auto-populated based on the Actions you have configured on the Actions tab of the settings page. You can see how to create Actions [here](https://github.com/facebook/ThreatExchange/wiki/Tutorial:-How-to-Notify-My-System-when-My-Content-Matches-a-Dataset#step-2---create-an-action-to-send-a-webhook)

## What Classifications are available and how to specify them
There are several types of Classification options that you can add to an Action rule to defien its logic. Currently, we support the follwoing types of Classifications

* DatasetID
   * If used with `=`,  the Action will only be run on a Match if the [MatchedSignal](Glossary#matcher) is in the the given Dataset. You can find the ID for a Dataset on the [ThreatExchange Settings page](ThreatExchange-Setting-Page)
   * If used with `≠`, the Action will not be run on a Match if the [MatchedSignal](Glossary#matcher) is in the the given Dataset

* Dataset Source
   * If used with `=`, the Action will only be run on a Match if the [MatchedSignal](Glossary#matcher) is in a Dataset that was from the given [Source](Glossary#fetcher)
   * If used with `≠`, the Action will not be run on a Match if the [MatchedSignal](Glossary#matcher) is from that Source
   * The following sources are available:
       * `te` for ThreatExchange

* MatchedSignal ID
   * If used with `=`, the Action will only be run on a Match if the [MatchedSignal](Glossary#matcher) has the given ID. This ID will be different for different Sources. If the Source of the Dataset is ThreatExchange (`te`) the MatchedSignal ID is the [Indicator](Glossary#fetcher) ID. You can view the MatchedSignal ID for a Match between a piece of Content and a Signal on the [Content Details page](Content-Details). The MatchedSignal ID is at the bottom of the page under "Matches"
   * If used with `≠`, the Action will not be run on a Match if the [MatchedSignal](Glossary#matcher) has the given ID.

* MatchedSignal
   * If used with `=`, the Action will only be run on a Match if the [MatchedSignal](Glossary#matcher) has the Classification. MatchedSignal objects can have one or more string Classifications associated with them such as `true_positive`. These Classifications are provided by the Source of the Dataset. If the Source is ThreatExchange, the MatchedSignal Classifications will be [Tags](Glossary#fetcher) on the [Indicator](Glossary#fetcher) 
   * If used with `≠`, the Action will only be run on a Match if the [MatchedSignal](Glossary#matcher) does not have the Classification.

