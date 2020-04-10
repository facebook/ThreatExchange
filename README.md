# Facebook ThreatExchange

ThreatExchange is a set of RESTful APIs on the Facebook Platform for querying, publishing, and sharing security threat information. It's a lightweight way for exchanging details on malware, phishing pages, and other threats with either specific members of the community or the ThreatExchange community at large.

This repository contains example code for using the API.

## Documentation

Full details on the ThreatExchange API, data formats, and best practices are available in the [ThreatExchange docs/](https://developers.facebook.com/docs/threat-exchange/).

## Example Code

This project offers example code in Java, Python, PHP, and Ruby.  There's also a reference client-side user interface to ThreatExchange, written in JavaScript. (A far richer featureset is available in the hosted [TE UI](https://developers.facebook.com/docs/threat-exchange/ui).)

## Get all available data

For tag-driven workloads, supporting either bulk download or incremental updates, our currently recommended best practice is a [Java reference design](https://github.com/facebook/ThreatExchange/blob/master/hashing/te-tag-query-java/README.md).

We also offer scripts in the `pytx/scripts` folder. For example, to get threat
descriptors uploaded to ThreatExchange run the following command:

```
$ python pytx/scripts/get_data.py -o threat_descriptor
```

## Blog

You can get details on the ThreatExchange platform, new features and other updates via our blog at [https://www.facebook.com/threatexchange](https://www.facebook.com/threatexchange).

## Getting Access

To request access to ThreatExchange, please submit an application via [https://developers.facebook.com/products/threat-exchange/](https://developers.facebook.com/products/threat-exchange/).

## License

Please see `./LICENSE`.
