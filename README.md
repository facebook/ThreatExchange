# Facebook ThreatExchange

ThreatExchange is a set of RESTful APIs on the Facebook Platform for querying, publishing, and sharing security threat information. It's a lightweight way for exchanging details on malware, phishing pages, and other threats with either specific members of the community or the ThreatExchange community at large.

For full details on ThreatExchange and best practices are available in the [ThreatExchange docs](https://developers.facebook.com/docs/threat-exchange/).

## API Reference Examples

The `api-reference-examples` folder contains example implementations in various languages for using the API. These implementations are at various stages of completeness and may not all implement every endpoint available on the ThreatExchange API. For full details on the ThreatExchange API and UI, data formats, and best practices are available in the [ThreatExchange docs](https://developers.facebook.com/docs/threat-exchange/).

## python-threatexchange

A python Library/CLI tool available on pypi under `threatexchange` which allows basic integration with ThreatExchange and matching on ThreatExchange signals.

## PDQ and TMK Hashing Technologies

ThreatExchange supports a variety of hashing algorithms for photos and videos. Two widely used algorithms are PDQ for photos and TMK for videos. The top-level folders `pdq` and `tmk` includes documentation and  implementation examples of these algorithms.

## Hasher-Matcher-Actioner (HMA)

This is a deployable project for bootstrapping content moderation, containing many sub parts. The initial capabilities support shared banks of image hashes kept in sync via ThreatExchange. Uses docker images (including proof-of-concept HMA-lite), as well as terraform configuration for setting up on AWS.


## Get All Available Data

For tag-driven workloads, supporting either bulk download or incremental updates, our currently recommended best practice is a [Java reference design](https://github.com/facebook/ThreatExchange/blob/main/api-reference-examples/java/te-tag-query/README.md).

You can also explore the dataset using the hosted [ThreatExchange UI](https://developers.facebook.com/docs/threat-exchange/ui)

## Getting Access

To request access to ThreatExchange, please submit an application via [https://developers.facebook.com/products/threat-exchange/](https://developers.facebook.com/products/threat-exchange/).

## Contributing

We welcome contributions! See [CONTRIBUTING](https://github.com/facebook/ThreatExchange/blob/main/CONTRIBUTING.md) for details on how to get started, and our [Code of Conduct](https://github.com/facebook/ThreatExchange/blob/main/CODE_OF_CONDUCT.md).

## License

All projects in this repository are under the BSD license - see [./LICENSE](https://github.com/facebook/ThreatExchange/blob/main/LICENSE). However, there are some exceptions for files that were included for demonstration purposes, and their alternative licenses are noted at the top of the files themselves.

As of 12/9/2021, this is the complete list of exceptions:
* pdq/cpp/CImg.h


