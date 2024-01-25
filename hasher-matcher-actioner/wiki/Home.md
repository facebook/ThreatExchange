## Introduction
![An diagram of HMA](https://user-images.githubusercontent.com/1654004/130529518-caaca375-9d06-4003-a2b9-7dbd35b663a6.png)

Hasher-Matcher-Actioner (HMA) is an open-source, turnkey trust and safety tool. You can submit content to your own instance of HMA to scan through content on your platform and flag potential community standards violations. You can configure rules in HMA to automatically take actions (such as enqueue to a review system) when these potential violations are flagged.

HMA can pull in lists of hashes from a variety of APIs, or make it simple to contribute hashes.

See also: [Meta's newsroom post about HMA](https://about.fb.com/news/2022/12/meta-launches-new-content-moderation-tool/)

### Why would I want HMA?
HMA can be either a tool in your existing content moderation strategy, or the starting point of a wider moderation ecosystem on your platform.
At it's core, HMA provides "similarity detection" or "copy detection", which allows detecting perceptually same or similar content that you (or someone else) has already seen. If the specific algorithms that HMA comes with only meet some of your needs, there are interfaces to plug into other solutions (including solutions that aren't just copy-detection, and can handle never-before-seen content), or to only use the subset of functionality you need.
Where HMA might shine is integrating with collaborative trust & safety solutions, such as [ThreatExchange](https://developers.facebook.com/docs/threat-exchange/).

#### What kinds of capabilities does HMA have?
Over time, HMA may gain more functionality. Additionally, HMA was designed to play nicely with other systems, and so missing functionality can be added by interfacing with other solutions. 

* ✅ Ready
* 🚧 In development or planned 2022
* 📋 Planned / Long Term

| Content Type | Matching Capability |  | | 
| --- | --- | --- | --- | 
| Photos  | ✅ PDQ  | 📋 PDQ+OCR | 
| Videos | ✅ MD5 | 📋 TMK+PDQF | 📋 vPDQ
| Text | 📋 Hamming | 📋 TLSH | 
| URL | 📋 Exact match | 📋 MD5 | 

### Where is the data hosted?
You run your own instance of HMA and have control of the contents you evaluate. You end up having to pay the hosting costs as a result. If someone else runs an instance and says you can call it, then they host the data.

HMA can download matching signals from APIs hosted by someone else.

#### How does HMA use external APIs?
If you configure it to, HMA will connect to external APIs (like ThreatExchange) to get signals and hashes to compare against. 

HMA does not share any data that you do not explicitly share by configuring it to do so. No metrics, no telemetry, etc. You can configure it to give feedback on signals that others have hosted (SEEN, true/false positive reporting), but it won't do so if you don't configure it to.

#### Can I use HMA without connecting to external APIs?
Yes, you can create your own collections of content and match against them without sending data outside of your platform.

### How long does it take to start using HMA?
You can get a test deployment up in roughly an hour, especially if you are already familiar with tools such as Terraform. 

The time to fully integrate into your infrastructure might require:
1. Setting up any custom AWS environment things you need (VPCs, routing, access controls, SSO)
2. Adding a hook in your content flow to trigger an API call for HMA to evaluate content.
3. Adding an endpoint in your admin tooling to receive callbacks from HMA to react to content it has flagged.
4. Setting configuration in HMA to download the right datasets and route matches.
5. Running some kind of experiment to slowly turn up traffic into HMA, make a judgement on the performance of the results.

A well-motivated engineer with access to all the resources they would need might take 1-2 weeks to do the above.

### What scale can HMA run at?
We have a target of processing 4k images/sec. In practice, we can currently hit 1.3k images/sec. However, the bottleneck is the hashing component. If you move the hashing to occur inside your own infrastructure, the "MA" version of HMA can hit 4k+ images/sec.

### How expensive is it to run HMA?
HMA is built off AWS lambda. If it's getting no traffic, it's almost-but-not-quite-free to run (queue polling events currently lead to ~$1 of charges a month in our testing, but please monitor and use limits in your setup).

As of last benchmarking in March 2021, the cost for 1MB images was 1 cent per 1000 images. Computing hashes in your own infrastructure can reduce the cost, as hashing is the most expensive component. 

### I already have some content moderation tools, and don't need all the bells and whistles.
You can only use the subsets of HMA that make sense for your platform. Check out [[What are the Different Ways that I Can Use HMA?]]

If AWS itself is a dealbreaker, you can try adapting the code to work with other clouds, or just use the underlying libraries, which live [in this same repo](https://github.com/facebook/ThreatExchange/tree/master/python-threatexchange).
