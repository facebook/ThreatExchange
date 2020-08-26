# Facebook ThreatExchange

ThreatExchange is a set of RESTful APIs on the Facebook Platform for querying, publishing, and sharing security threat information. It's a lightweight way for exchanging details on malware, phishing pages, and other threats with either specific members of the community or the ThreatExchange community at large.

For full details on ThreatExchange and best practices are available in the [ThreatExchange docs](https://developers.facebook.com/docs/threat-exchange/).

## API Reference Examples

The `api-reference-examples` folder contains example implementations in various languages for using the API. These implementations are at various stages of completeness and may not all implement every endpoint availible on the ThreatExchange API. For full details on the ThreatExchange API and UI, data formats, and best practices are available in the [ThreatExchange docs](https://developers.facebook.com/docs/threat-exchange/).

## pytx3

`pytx3` is an all-in-one python package CLI which allows basic integration with ThreatExchange including matching on publically availible data.

## PDQ and TMK Hashing Technologies

ThreatExchange supports a variety of hashing algorithms for photos and videos. Two widely used algorithms are PDQ for photos and TMK for videos. The top-level folders `pdq` and `tmk` includes documentation and  implementation exampels of these algorithms.

## Get All Available Data

For tag-driven workloads, supporting either bulk download or incremental updates, our currently recommended best practice is a [Java reference design](https://github.com/facebook/ThreatExchange/blob/master/api-reference-examples/java/te-tag-query/README.md).

You can also explore the dataset using the hosted [ThreatExchange UI](https://developers.facebook.com/docs/threat-exchange/ui)

## Getting Access

To request access to ThreatExchange, please submit an application via [https://developers.facebook.com/products/threat-exchange/](https://developers.facebook.com/products/threat-exchange/).

## License

Please see `./LICENSE`.
