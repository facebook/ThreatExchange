# python-threatexchange

A Python Library to simplify the exchange and use of trust & safety information, especially media hash exchanges. It also contains a CLI called `threatexchange` to demonstrate the functionality.

python-threatexchange is designed to be extensible and comes with a simple model of adding new functionality.

To get similar functionality in a deployable service, check out hasher-matcher-actioner.

![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/facebook/ThreatExchange/python-threatexchange-ci.yaml?branch=main) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/threatexchange) ![PyPI - Downloads](https://img.shields.io/pypi/dm/threatexchange) ![PyPI](https://img.shields.io/pypi/v/threatexchange) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) 

## Run the CLI in Docker container

A Dockerfile is provided which allows you to run the CLI with minimal dependencies.

First build the container:
```
$ docker build --tag threatexchange .
```

Then run:
```
$ docker run threatexchange
```

To persist the configuration and data between invocations, mount the `/var/lib/threatexchange` volume:

```
$ docker run --volume $HOME/.threatexchange:/var/lib/threatexchange
```


## Installation

If you don't have `pip`, learn how to install it [here](https://pip.pypa.io/en/stable/installation/).

```bash
$ python3 -m pip install threatexchange --upgrade
```

# Introduction
Trust and safety is a generally hard problem. An issue that makes the problem harder is that most platforms attempt to keep their platforms safe on their own, despite bad actors and viral content spreading from platform to platform. This results not only in duplicate effort in building out technical capability to detect harmful content, but also duplicate effort in preventing the spread of known harmful content, since each platform is fighting potentially the same copies of content on their own.

One technique that can allow platforms to combine efforts to combat harm is by sharing signatures of content that they have already detected on their own, or the inputs to various trust and safety tools that can be used to find harmful content. The most well-known are photo/video hash sharing programs like those operated by the National Center for Exploited and Missing Children (NCMEC) and the Global Internet Forum to Counter Terrorism, Southwest Grid for Learning’s StopNCII.org and Meta's ThreatExchange platform.

The python-threatexchange library aims to simplify the exchange of signals via platforms like the above, as well as provide a baseline of functionality available to simplify the testing and creation of new exchanges and techniques, as well as provide cross-compatibility. 

## Philosophy of the Library
This library is maintained by a small team at Meta with a limited range of experience, and so we will prioritize the use cases we are most familiar with. We believe that accessibility is a barrier for many platforms and so will put as much as we can in the open. We also understand that it may not make sense to use only publicly visible approaches, and welcome platform-specific modifications and derivatives. However, we also accept pull requests! If you think functionality is widely applicable, or you have a bug bothering you, we accept pull requests! If you are thinking a larger change may be needed (such as adding an entirely new subcommand to the CLI), we appreciate if you reach out to talk through a feature before submitting it!

# Key Concepts

Below is a quick overview of the key concepts. If you dig deeper into the library, there are additional considerations that might apply if you are creating your own extensions.

![basic concepts](https://user-images.githubusercontent.com/1654004/182606322-b7b4e627-c21f-47da-ac8c-f6a57d8ba9c6.png)

The basic flow of data through the system is:
1. Configure which sources of data (signals) you want to pull from (aka collaborations)
2. Download from all sources
3. Store the signals and build an efficient matching datastructure (index)
4. Match content against stored signals

### Collaborations
A collaboration represents a single collection of data from a single API. This often ties to practical usage such as "A1 video hashes from the NCMEC industry database" or "terrorism photo hashes from Meta's ThreatExchange only from specific applications". In cases where a platform may want to test or take different actions on matching data from one location, Collaborations provide a way to do so. 


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

### Extensions
This library can make use of extensions provided by any party, public or private, as long as they conform to the conventions established in the library. Extensions are a way to prototype out new techniques, and quickly make them available in existing exchanges. Some exchanges, like ThreatExchange, allow sharing arbitrary data with arbitrary labels, and so a new technique can be rapidly demonstrated cross-platform even if not officially supported. 


# `threatexchange` CLI

The `threatexchange` cli is designed to rapidly demonstrate the value of the library, and if you were in a pinch, could be the basis for an end-to-end solution if needed.


## Usage

While the CLI was designed for use with signal exchanges. The normal flow is roughly: 
1. configure collaborations
2. fetch from APIs
3. build indices 
4. match data
5. contribute labels and data

```bash
$ threatexchange --help  # The help should give a decent overview of functionalities

# Step 1: We can skip this step if using the sample data
$ threatexchange collab edit ...

# Step 2: This will save progress, and we'll want to rerun it to get new data periodically
$ threatexchange fetch

# Step 3: This is done by default at the end of step 2, but you can also trigger it manually
$ threatexchange dataset --rebuild-indices

# Step 4: You can match a variety of content and formats
$ threatexchange match text -- 'bball now?'
raw_text - (Sample Signals) INVESTIGATION_SEED
trend_query - (Sample Signals) INVESTIGATION_SEED
# You can also debug matching by looking at what hashes are generated:
$ threatexchange hash video example.mp4
video_md5 f09791b743c21f26a189c33b798b8e46

# Step 5: Contribute labels 
$ threatexchange label ...
```

### Viewing Signals
TODO
```
$ threatexchange dataset 
$ threatexchange dataset -P --csv > out.csv
```

### Connecting to APIs and Getting Signals

#### A local file
This is the fastest way to experiment with the CLI functionality and saving contents

```
$ threatexchange hash photo https://github.com/facebook/ThreatExchange/blob/main/pdq/data/misc-images/b.jpg?raw=true
pdq f8f8f0cee0f4a84f06370a22038f63f0b36e2ed596621e1d33e6b39c4e9c9b22
$ threatexchange hash photo https://github.com/facebook/ThreatExchange/blob/main/pdq/data/misc-images/b.jpg?raw=true >> ~/file.txt
$ threatexchange config collab edit local_file --filename ~/file.txt 'file.txt' --create
$ threatexchange fetch
$ threatexchange match photo https://github.com/facebook/ThreatExchange/blob/main/pdq/data/misc-images/b.jpg?raw=true
pdq - (file.txt) INVESTIGATION_SEED
```

#### ThreatExchange
If you have access to [Meta's ThreatExchange](https://developers.facebook.com/programs/threatexchange/), you can use the library with [PrivacyGroups](https://developers.facebook.com/docs/threat-exchange/reference/apis/threat-privacy-group) with [threat_updates](https://developers.facebook.com/docs/threat-exchange/reference/apis/threat-updates/) enabled.

```
# Step 1 - configure the default credentials
$ threatexchange config api fb_threat_exchange --access-token '<TOKEN>'
# Step 1 Alternative 1 - TX_ACCESS_TOKEN Environment variable
$ TX_ACCESS_TOKEN='<TOKEN>'
$ export TX_ACCESS_TOKEN

# Step 1 Alternative 2 - ~/.txtoken file
$ touch ~/.txtoken
$ chmod 600 ~/.txtoken
$ echo '<TOKEN>' > ~/.txtoken file

# Step 2 - import configuration
$ threatexchange config api fb_threat_exchange -L
1012185296055235 'Example Collaboration' ...
$ threatexchange config api fb_threat_exchange -I 1012185296055235

# Step 2 Alternative - manually configure via
$ threatexchange config collab edit fb_threatexchange ...

$ threatexchange fetch
```

#### NCMEC Hash API
The [National Center for Exploited and Missing Children (NCMEC)](https://www.missingkids.org/) hosts a number of media hash exchanges related to Child Sexual Abuse Material (CSAM). If you have an account with NCMEC and credentials, you download and use hashes from that API.

```
# Step 1 - configure the default credentials
$ threatexchange config api ncmec --credentials '<USER>' '<PASSWORD>'
# Step 1 Alternative 1 - TX_NCMEC_CREDENTIALS Environment variable
$ TX_NCMEC_CREDENTIALS='<TOKEN>'
$ export TX_NCMEC_CREDENTIALS

# Step 2 - set up config
# Example: NGO database only using esp=1
$ threatexchange config collab edit ncmec --create 'NCMEC NGO' --environment=NGO --only-esp 

$ threatexchange fetch
```

#### StopNCII.org
[StopNCII.org](https://stopncii.org/) allows people to upload hashes of intimate imagery/videos when someone is threatening to share them. If you are a partner with credentials, you can download and use hashes from that API.

```
# Step 1 - TX_ACCESS_TOKEN Environment variable - comma separated
$ TX_STOPNCII_KEYS='<FUNCTION_KEY>,<SUBSCRIPTION_KEY>'
$ export TX_STOPNCII_KEYS

# Step 1 Alternative - ~/.tx_stopncii_keys file
$ touch ~/.tx_stopncii_keys
$ chmod 600 ~/.tx_stopncii_keys
$ echo '<FUNCTION_KEY>,<SUBSCRIPTION_KEY>' > ~/.tx_stopncii_keys

# Step 2 - set up config
$ threatexchange config collab edit stop_ncii --create 'StopNCII' 

$ threatexchange fetch
```

## Appendix 
### State
The CLI stores state in `~/.threatexchange`. There are a few commands which will manipulate this directory, but if you need to factory reset, do `rm -r ~/.threatexchange`

## General Expectation for Compatibility and Versioning
We strive to provide a stable library for use in production systems. To that end, we will use version numbers to help platforms which are using the threatexchange libraries in their own codebase.

Public Interfaces:
* Any API used in extensions (SignalType, ContentType, etc), including their names and paths.
  * Implementations of those APIs in the library (i.e. PDQSignal), (though excluding internal details of those implementations) 
* CLI commands and flags
  * CLI output format that might be part of a pipeline (ex: `threatexchange dataset -P` and `threatexchange match` stdout) 
* CLI state

Private Interfaces/Internal Details:
* CLI command implementations
* CLI Logging/stderr
* Any CLI behavior marked as unstable, prototype, or draft in its --help

1. Major versions (1.X.X => 2.0.0) Will have breaking changes
   1. Extensions (SignalType, ContentType, SignalExchangeAPI) may not be backwards compatible
   2. State (FetchedSignalMetadata, file formats): May not be compatible, but libraries or the CLI may attempt to automatically migrate if possible. Tooling to migrate state may also be available.
   3. CLI: Storage formats, commands, may all have changed.
   4. Library: Files may be moved or renamed
2. Minor versions (1.0.X => 1.1.X) May change public interfaces, but only in ways that are backwards compatible
   1. Extensions: May gain new methods, or have signatures with new arguments with defaults
   2. State: May be changed only if automatic migration is possible with how the CLI uses it (`__setstate__` with pickle, TBD with dacite)
   3. CLI: Flags may change behavior or move only if previous invocations will do the same thing (i.e. nargs could go from 1 to '*' or '+', or the flag can be renamed if a hidden alias is maintained)
   4. Library: Files not in the public interface may be moved or renamed.
3. Revision numbers (1.0.0 => 1.0.1) will be fully backwards compatible.


### The CLI as an E2E Solution
While hasher-matcher-actioner is this repository's attempt at a scaled end-to-end solution, the CLI uses the same libraries and can emulate the same functionality.

In order to do that, you'll need to solve a few problems:
1. Storing and potentially distributing config files 
2. Calling `threatexchange fetch` periodically
3. Distributing the produced indices
4. Connecting your content pipeline to `threatexchange match` from those indices
5. Routing matches to your own tooling and infrastructure.

Unless you are doing the above on a single machine, your favorite distributed filesystem may handle most of these problems (for example, syncing a single shared ~/.threatexchange directory).
