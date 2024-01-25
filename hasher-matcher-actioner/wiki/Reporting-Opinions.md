[Opinions](Glossary#writebacker) are subjective decisions made by a [Platform](Glossary#terms-and-concepts-used-in-hma) about a [Match](Glossary#matcher). Currently, users can report two Opinions about a Match: [TruePositive](Glossary#writebacker) and [FalsePositive](Glossary#writebacker). A TruePositive Opinion indicates that the Platform believes that the [Signal](Glossary#hasher) rightfully belongs to the [Dataset](Glossary#matcher) it has matched to. A FalsePositive Opinion indicates that the Platform believes that the Signal should not be in the Dataset it has matched to.

# Why Provide Opinions about Content?
There are two reasons to provide Opinions on Matches. First, it can save time reviewing similar Content. For example, let's say an image is uploaded to your Platform and it Matches the cat Dataset. You then review it and determine that it is, in fact, an image of a cat so you mark it as TruePositive. If, then, the same image is uploaded again, and Matches the same Signal in the cat Dataset, you already know it is a cat and can take an appropriate [Action](Glossary#actioner) without having to review the same Content again.

The second reason to provide Opinions is to make the entire internet safer. There are many problems in the Trust & Safety space that affect all Platforms jointly, and lead to real world harm. Opinion-sharing reduces this harm by helping Platforms prioritize which Content to review. Platforms come in all shapes and sizes, and not all can afford to hire a myriad of reviewers or invest millions in specialized machine learning models. For Platforms with limited resources, seeing multiple other Platforms think that an image is harmful (marked TruePositive) can help them prioritize which Content to review. Similarly, marking a Match as FalsePositive can help improve the quality of the Datasets.

Even for Platforms which already have robust Trust & Safety programs, there are still tangible benefits to sharing Opinions. Namely, the harmful Content found on those Platforms often doesn’t go away, it just goes somewhere else. A rising tide lifts all boats, and by all pitching in, we can improve the baseline safety level for the entire internet. Even if you aren’t uploading new Signals, simply marking TruePositive or FalsePositive will improve that baseline, build trust in our Platforms, and help make the internet safer.

# How to Provide Opinions about Content

It's easy to report Opinions through the HMA UI. From the [Content Details Page](Content-Details) page, you can view all Matches for a piece of Content. Click the Opinion button for a Signal row and mark the Content as TruePositive or FalsePositive. When you do so, the Source of the Matched Dataset will be notified of your Opinion.

A few things to note:
- You cannot change an opinion directly from TruePositive to FalsePositive (or vice-versa). You must first remove the TruePositive, wait for the changes to propagate, then mark FalsePositive.
- Opinions correspond to Signals not to [Content](Glossary#hasher). Since a single piece of Content can Match multiple [Datasets](Glossary#matcher) and can Match multiple Signals within a single Dataset, one piece of Content can result in individuals Signals marked as both TruePositive and FalsePositive.
- After you provide an Opinion for a Signal, it can take several minutes to save as the Source of the Dataset is notified. While your Opinion is being sent to the Source and being read again, you cannot update the Opinion. This can take several minutes depending on how often you are Fetching data. While your Opinion is being propagated, the box will appear grey.

![](https://github.com/facebook/ThreatExchange/blob/master/hasher-matcher-actioner/docs/images/Content%20Details%20Page.png)

![](https://github.com/facebook/ThreatExchange/blob/master/hasher-matcher-actioner/docs/images/Remove%20Opinion.png)
