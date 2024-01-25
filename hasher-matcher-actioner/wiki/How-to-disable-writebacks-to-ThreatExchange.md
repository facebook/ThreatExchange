So, you have setup the HMA instance within your AWS account and are submitting content and getting flagged photos. But you want to stop reporting the `saw_this_too` opinion to [ThreatExchange](https://developers.facebook.com/docs/threat-exchange/getting-started). Here's how you go about doing that.


* From the HMA UI, click on the settings link on the bottom left of the page, go to ThreatExchange tab

![](https://github.com/facebook/ThreatExchange/blob/31d8c61a3f5c8f746db772157bf13f311bf1969c/hasher-matcher-actioner/docs/images/ThreatExchange%20tab.png)

* To turn on and off ```saw_this_too``` and opinion change write backs toggle _**Writeback(Seen?)**_
    * This will need to be done individually for all desired datasets
<img src="/facebook/ThreatExchange/blob/master/hasher-matcher-actioner/docs/images/HMA-TESettings-Privacy-Group-WritebackSeen-highlight.png?raw=true" alt="HMA-TESettings-Privacy-Group-WritebackSeen-highlight.png" width="555" height="492">

### That's it, you're all set!


