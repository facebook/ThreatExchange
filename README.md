# Projects in this Repository

This repository originally started as code to support Meta's ThreatExchange API, but over time has grown to include a number of projects to support signal exchange and content moderation in general. Below are a list of sub-projects.

## PDQ Image Hashing and Similarity Matching

PDQ is a photo hashing algorithm that can turn photos into 256 bit signatures which can then be used to match other photos.

## TMK+PDQF (TMK) Video Hashing and Similarity Matching

TMK+PDQF (or TMK for short) is a video hashing algorithm that can turn videos into 256KB signatures which can be used to match other videos.

## Video PDQ (vPDQ) Video Hashing and Similarity Matching

Video PDQ (or vPDQ for short) is a simple video hashing algorithm that determines two videos are matching based on the amount of shared similar frames. It can easily be applied for other image algorithms, and not just PDQ.

## Hasher-Matcher-Actioner (HMA) Trust & Safety Platform

HMA is a ready-to-deploy content moderation project for AWS, containing many submodules. It allows you to maintain lists of known content to scan for, which you can either curate yourself or connect to other hash exchange programs to share and recieve lists.  More can be found [at the wiki](https://github.com/facebook/ThreatExchange/wiki).

A second version of this project, called "[Open Media Match](https://github.com/facebook/ThreatExchange/tree/main/open-media-match)" is under construction, which uses a cloud-agnostic docker-based deployment.

## python-threatexchange

A python Library/CLI tool available on pypi under `threatexchange` which provides implementations for content scanning and signal exchange. It provides reference implementations in python for downloading hashes from Meta's ThreatExchange API, scanning images with PDQ, and others. It can also be easily extended to work with other hash exchanges and other techniques, not all of which are written by the maintainers of this repository.


## Meta's ThreatExchange API Reference Examples

The `api-reference-examples` folder contains example implementations in various languages for using the API. These implementations are at various stages of completeness and may not all implement every endpoint available on the ThreatExchange API. For full details on the ThreatExchange API and UI, data formats, and best practices are available in the [ThreatExchange docs](https://developers.facebook.com/docs/threat-exchange/).

# Meta's ThreatExchange API
ThreatExchange is a set of RESTful APIs on the Facebook Platform for querying, publishing, and sharing security threat information. It's a lightweight way for exchanging details on malware, phishing pages, and other threats with either specific members of the community or the ThreatExchange community at large.

For full details on ThreatExchange and best practices are available in the ThreatExchange docs.

## Get All Available Data

For tag-driven workloads, supporting either bulk download or incremental updates, our currently recommended best practice is a [Java reference design](https://github.com/facebook/ThreatExchange/blob/main/api-reference-examples/java/te-tag-query/README.md).

You can also explore the dataset using the hosted [ThreatExchange UI](https://developers.facebook.com/docs/threat-exchange/ui)

## Getting Access

To request access to ThreatExchange, please submit an application via [https://developers.facebook.com/products/threat-exchange/](https://developers.facebook.com/products/threat-exchange/).

# Other Information about this Repository
## Contributing

We welcome contributions! See [CONTRIBUTING](https://github.com/facebook/ThreatExchange/blob/main/CONTRIBUTING.md) for details on how to get started, and our [Code of Conduct](https://github.com/facebook/ThreatExchange/blob/main/CODE_OF_CONDUCT.md).

## License

All projects in this repository are under the BSD license - see [./LICENSE](https://github.com/facebook/ThreatExchange/blob/main/LICENSE). However, there are some exceptions for files that were included for demonstration purposes, and their alternative licenses are noted at the top of the files themselves.

As of 12/9/2021, this is the complete list of exceptions:
* pdq/cpp/CImg.h


