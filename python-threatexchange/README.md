# python-threatexchange

A Python Library for downloading and using datasets stored in ThreatExchange.

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Overview
Fetching signals from ThreatExchange "correctly" is sadly not as straightforward as it should be.

Additionally, once you have the data, the application of those signals can be difficult.

This library provides a reference implementation for fetching datasets, applying many common formats, and uploading your own signals to the dataset.

These reference implementations are not meant to be the best, most efficient, or production ready versions, but to instead be simple enough that they could be easily pasted to other languages.

The bundled cli tool of the same name is meant to demonstrate the library, as well as potentially provide a first draft implementation for prototype or evaluation.

## Installation

If you don't have `pip`, learn how to install it [here](https://pip.pypa.io/en/stable/installation/).

```bash
$ python3 -m pip install threatexchange [--upgrade]
```

The base installation includes matching for:

**Text**
* Raw Text
* Trend Queries

**URL**
* URLs (simple)

**Photo**
* MD5

**Video**
* MD5

### Expansions
You can install additional libraries to add to the number of matching SignalTypes supported:
* `pdqhash` - Adds Photo PDQ
* `pdqhash`, `tesseract` - Adds Photo PDQ+OCR


## Usage
This package can be used as a library, but the fastest way to use it is from the CLI.

Before the CLI will work, you need to [get access to ThreatExchange](https://developers.facebook.com/programs/threatexchange), and then store your App's [access token](https://developers.facebook.com/tools/accesstoken/) in either an environment variable named `$TXTOKEN` or a file called `.txtoken` in the home directory.

```bash
$ threatexchange match text "bball now?"
Looks like you haven't set up a collaboration config, so using the sample one against public data
Looks like you are running this for the first time. Fetching some sample data.
video_md5: 2
raw_text: 3
url: 1
video_tmk_pdqf: 1
photo_md5: 1
pdq: 138
trend_query: 1
3425830734108278 raw_text media_priority_samples
3261912580534814 trend_query media_priority_samples

$ threatexchange label descriptor 3425830734108278 false_positive
```

## Key Concepts
This library extends some of the concepts from the [ThreatExchange API](https://developers.facebook.com/docs/threat-exchange/reference/apis/) to facilitate content and hash matching. ThreatExchange has a very generic data model, of which the usage has mostly been defined by convention. This library allows for encoding common conventions.

### Matching Algorithms
This library implements multiple matching algorithms, which take in indexes of Signal Types, and then attempt to find matches on content. Signals can be exchanged via the ThreatExchange platform as part of a Collaboration. Many matching algorithms use a one-way algorithm on content to produce a smaller, anonymized, intermediate object, often referred to as "hashing" and a "hash" respectively. This library uses "SignalType" and "Signal" in many similar contexts as a generalization.

### Collaboration Config
ThreatExchange has a concept of privacy, enforced through visibility. The most common way ThreatExchange signals are exchanged is through the [PrivacyGroup](https://developers.facebook.com/docs/threat-exchange/reference/apis/threat-privacy-group/) concept. However, the visibility is only half of the need of these groups - establishing common conventions (how to interpret the data, such as through labeling the with the ThreatTags feature).

This library encodes both the visibility and the conventions into a file that can then handle the specific details of the collaboration. A collaboration config might look like this:
```json
{
  "name": "Example Collaboration",
  "labels": {
    "media_priority_samples": {},
    "example_label_a": {},
    "example_label_b": {}
  },
  "privacy_groups": [123456789]
}

```

Which establishes that there are three valid labels for this collaboration (of which all data should have at least one), and that uploaded data should be shared in privacy group 123456789.

### Signal Type and Signals
Signals are inputs to matching algorithms that will run against content. SignalType is an abstraction that covers both the algorithm that produces signals from content, as well as the matching algorithm itself. For example, the PhotoMD5 SignalType contains both the hashing algorithm (md5) to convert photos to MD5s, the serialization of photo MD5s in ThreatExchange, as well as comparing MD5s from stored Signals and matched content.

In ThreatExchange, data is stored as [ThreatIndicators](https://developers.facebook.com/docs/threat-exchange/reference/apis/threat-indicator). ThreatIndicators have a type, such as HASH_MD5, which indicate what the data represents. However, there may be types that haven't been encoded yet as ThreatIndicators in ThreatExchange, and so a convention on what they represent must be established. For example, for media hashing, Photo MD5s and Video MD5s are two different types of MD5s, and you probably don't want to combine the two. To solve this, collaborations often come up with conventions using ThreatTags to resolve the two. For example, a photo md5 hash could have the tag "media_type_photo" added to it. However, ThreatTags can only be applied at the [ThreatDescriptor](https://developers.facebook.com/docs/threat-exchange/reference/apis/threat-descriptor) level.

This ends up making the API interactions complicated. To deal with this, the library (and CLI) simply group everything by Signal Type, and each algorithm just takes one or more Signal Types as inputs.

### Content Type
Content Types are classes of inputs to matching algorithms, of which the result can be either "match" or "no match", with an optional distance, the meaning of which differs by algorithm.

Some matching algorithms can run on multiple content types, but most work on just a single content type.

Example:
1. Text - Raw Text and Trend Query can run against this.
2. Photo - Photo MD5 and Photo PDQ can run against this, but Raw Text or Trend Query might also apply (if going against OCR data).

### Collaborative Signal Datasets
This library and tool are designed to be used to demonstrate collaborative signal datasets. This is where multiple contributors are adding labels on signals and uploading them to ThreatExchange. If multiple contributors are labeling, there is a possibility of disagreement or partial agreement.

In many advanced cases, you may want to filter signals that are disputed, or only contributors you trust. This library applies several shorthand labels to signals for the most common filters.

1. true_positive - This label is added if you are the one that contributed this signal to the dataset (unless you marked it as a false positive)
2. false_positive - This label is added if you indicated the signal is a false positive OR if all labels are false positive.
3. disputed - This label is added if a contributor (other than yourself) marked the signal as a false positive

```bash
$ threatexchange match photo example_disputed.jpg
8313378 photo_pdq example_label_a disputed

$ threatexchange match photo example_disputed.jpg  --hide-disputed

$ threatexchange label descriptor 8313378 false_positive
8313379 photo_pdq false_positive

$ threatexchange match photo example_disputed.jpg

$ threatexchange match photo example_disputed.jpg --show-false-positives
8313378 photo_pdq example_label_a false_positive

$ threatexchange label descriptor 8313378 example_label_b
8313378 photo_pdq example_label_b true_positive  # If you gave a label, only yours is shown
```
