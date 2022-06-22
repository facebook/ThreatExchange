# python-threatexchange

A Python Library to simplify the exchange and use of trust & safety information, especially media hash exchanges. It also contains a CLI called `threatexchange` to demonstrate the functionality.

python-threatexchange is designed to be extensible and comes with a simple model of adding new functionality.

To get similar functionality in a deployable service, check out hasher-matcher-actioner.

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/threatexchange) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) 

## Please Pardon Our Dust
ThreatExchange is in the middle of a big refactor starting in #944 and isn't fully stable yet. Track progress at https://github.com/facebook/ThreatExchange/projects/3

## Installation

If you don't have `pip`, learn how to install it [here](https://pip.pypa.io/en/stable/installation/).

```bash
$ python3 -m pip install threatexchange [--upgrade]
```

# Introduction
Trust and safety is a generally hard problem. An issue that makes the problem harder is that most platforms attempt to keep their platforms safe on their own, despite bad actors and viral content spreading from platform to platform. This results not only in duplicate effort in building out technical capability to detect harmful content, but also duplicate effort in preventing the spread of known harmful content, since each platform is fighting potentially the same copies of content on their own.

One technique that can allow platforms to combine efforts to combat harm is by sharing signatures of content that they have already detected on their own, or the inputs to various trust and safety tools that can be used to find harmful content. The most well-known are photo/video hash sharing programs like those operated by the National Center for Exploited and Missing Children (NCMEC) and the Global Internet Forum to Counter Terrorism, Southwest Grid for Learning’s StopNCII.org and Meta's ThreatExchange platform.

The python-threatexchange library aims to simplify the exchange of signals via platforms like the above, as well as provide a baseline of functionality available to simplify the testing and creation of new exchanges and techniques, as well as provide cross-compatibility. 

## Philosophy of the Library
This library is maintained by a small team at Meta with a limited range of experience, and so we will prioritize the use cases we are most familiar with. We believe that accessibility is a barrier for many platforms and so will put as much as we can in the open. We also understand that it may not make sense to use only publicly visible approaches, and welcome platform-specific modifications and derivatives. However, we also accept pull requests! If you think functionality is widely applicable, or you have a bug bothering you, we accept pull requests! If you are thinking a larger change may be needed (such as adding an entirely new subcommand to the CLI), we appreciate if you reach out to talk through a feature before submitting it!

## General Expectation for Compatibility and Versioning
1. Major versions (1.X.X => 2.0.0) are not guaranteed to be backwards compatible. However, post 1.0.0, tooling to try and migrate state forward will be available. Please reach out if you need help migrating forward. 
2. Minor versions (1.0.X => 1.1.X) will be backwards compatible, with the exception that CLI flags or commands may be renamed if it's not feasible to provide an alias

# Key Concepts

Below is a quick overview of the key concepts. If you dig deeper into the library, there are additional considerations that might apply if you are creating your own extensions.


### SignalType, Signals, Indices
A SignalType is the encapsulation of a technique that can be used to classify or detect content and the settings for detecting that content can be shared between platforms.

A serialization of data that can be used as an input to detect/match content is called a "signal", and this library enforces that every signal be representable has a python str class.

SignalType enforces that you provide "naive" or brute force versions of the techniques that can be used for correctness testing. By default, python-threatexchange will use a simple linear scan against these brute force methods. If there are more efficient methods for scanning large datasets, the SignalTypeIndex interface provides a place to store a more complex scaled technique.

### ContentType, Content
SignalTypes are usually not globally applicable, targeting only a specific type of content such as text, images, or URLs. Additionally, some types of content can be decomposed or processed to extract additional content. Take for example a URL to a post on a social media site with an embedded video hosted on a third site with a description and thumbnail. 

```
URL: www.example.com/post/123
              |
              +-- Text: "Look at this cool video"
              |
              +-- Photo: <thumbnail preview>
              |
              +-- URL: www.content-host.com/321.mp4
                                 |
                                 + File: 321.mp4
                                           |
                                           + Video: <bytes>
                                                       |
                                                       + Images: <frame1>, <frame2>...
                                                       |             |
                                                       |             + Text: <from OCR>
                                                       |
                                                       + Audio: <bytes>
                                                                   |
                                                                   + Text: <computer generated transcript> 
```

ContentType is a wrapper around traversing this graph and helping find out which techniques are applicable given a given input. It may make sense to create ContentTypes specific to your platform (such as a post type), or to represent specific combinations of signals. Certain imagery may only be harmful if accompanied by certain text and vice-versa.

### SignalExchangeAPI, Updates, Checkpoints, FetchedMetadata, Storage
A SignalExchangeAPI is a location that allows for the exchange of Signals. It's not expected that that every SignalExchangeAPI supports all signals, or that it is hosted by a third party - an API could just be a specific file on disk. 

The interface defines how a full copy of signals for a single Collaboration can be fetched using sequential, checkpoint-able updates. It also must provide a solution for naive implementations of storage by merging a copy of the data in memory. 

For some applications, the amount of data will be too large to fit in memory - in that case, a solution that can efficiently merge updates produced by the fetch() function is all that is needed.

### Collaborations
A collaboration represents a single collection of data from a single API. This often ties to practical usage such as "A1 video hashes from the NCMEC industry database". In cases where a platform may want to test or take different actions on matching data from one location, Collaborations provide a way to do so.  


### Extensions
This library can make use of extensions provided by any party, public or private, as long as they conform to the conventions established in the library. Extensions are a way to prototype out new techniques, and quickly make them available in existing exchanges. Some exchanges, like ThreatExchange, allow sharing arbitrary data with arbitrary labels, and so a new technique can be rapidly demonstrated cross-platform even if not officially supported. 


# `threatexchange` CLI

The `threatexchange` cli is designed to rapidly demonstrate the value of the library, and if you were in a pinch, could be the basis for an end-to-end solution if needed.


## Usage

While the CLI was designed for use with signal exchanges, it also comes with a built-in copy of data that is loaded 

```bash
$ threatexchange --help  # The help should give a decent overview of functionalities

# You can immediately begin matching against text data
$ threatexchange match text -- 'bball now?'
<stderr omitted>
raw_text - (Sample Signals) WORTH_INVESTIGATING
trend_query - (Sample Signals) WORTH_INVESTIGATING

# Hashing is also available out of the box
$ threatexchange hash video example.mp4
video_md5 f09791b743c21f26a189c33b798b8e46
```

## State
The CLI stores state in `~/.threatexchange`. There are a few commands which will manipulate this directory, but if you need to factory reset, do `rm -r ~/.threatexchange`

## As an E2E Solution
While hasher-matcher-actioner is this repository's attempt at a scaled end-to-end solution, the CLI uses the same libraries and can emulate the same functionality.

In order to do that, you'll need to solve a few problems:
1. Storing and potentially distributing config files 
2. Calling `threatexchange fetch` periodically
3. Distributing the produced indices
4. Connecting your content pipeline to `threatexchange match` from those indices
5. Routing matches to your own tooling and infrastructure.

Unless you are doing the above on a single machine, your favorite distributed filesystem may handle most of these problems (for example, syncing a single shared ~/.threatexchange directory).
