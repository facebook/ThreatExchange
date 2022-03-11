---
sidebar_position: 1
---

# Introduction

Hasher-Matcher-Actioner (HMA) is an open-source, trust and safety tool. You submit content to HMA. It scans the content and flags potential community standards violations. Configure rules in HMA to automatically take actions (such as enqueue to a review system) when these potential violations are flagged.

# When to use HMA?

If the following is true about your organization, then you need HMA.
* You support online communties like Meta does
* You have community standards / guidelines or rules that you would like to enforce

# How does HMA enforce your community standards?

HMA allows you to create collections of media objects (photos or videos) that must be flagged if they appear on your platform. Internally, HMA creates unique fingerprints of these media objects and scans your platform for them. If it finds identical or nearly identical media, it flags them to your staff or systems.

# Wait, I don't want to send my user's content to you!

No worries! HMA is installed in your AWS cloud account. Your user's content never leaves your infrastructure.