Stopping or Pausing HMA is easy but requires you to know exactly what you want to stop.

# Stop [Matching](Glossary#matcher) (and subsequent [Actions](Glossary#actioner))
To stop Matching on all [Content](Glossary#hasher) flowing into HMA, navigate to the [ThreatExchange Settings Page](ThreatExchange-Settings-Page) and, for each [PrivacyGroup](Glossary#fetcher), switch the "Matcher Active" toggle off. This will stop Matching all Content against that Dataset.

# Stop Sending Actions
To stop performing Actions as the result of a Match but continue matching, delete all the [ActionRules](Glossary#actioner) from [the ActionRules Page](The-Action-Rules-Page#delete-an-action-rule). This will still log when Matches occur, but no Actions will be executed.

# Stop Fetching From ThreatExchange
To stop Fetching updates for a [Dataset](Glossary#matcher), if that Dataset originated from a [ThreatExchange](Glossary#fetcher) PrivacyGroup, navigate to the [ThreatExchange Settings Page](ThreatExchange-Settings-Page) and, for each PrivacyGroup, switch the "Fetcher Active" toggle off. While off, no new Signals will be read from ThreatExchange, and no Signals will be deleted when they are removed from ThreatExchange. The Dataset will continue to Match Content if the "Matcher Active" toggle is on.

# Shut it all down... PERMANENTLY
We can't imagine any reason why you would ever want to shut down HMA, but if truly necessary, you can do so with a simple command. However before doing so please think carefully and read these important obligatory warnings!

**This will _permanently_ delete EVERYTHING in HMA - all data and all configurations. It will wipe AWS clean**

**Make _really, really_ sure you want to do this and you don't want to just pause HMA using the steps above**

So, if you're sure, run the following command in the same location you first cloned this repo and installed HMA:

```
$ terraform -chdir=terraform destroy
```

It's that easy... and dangerous