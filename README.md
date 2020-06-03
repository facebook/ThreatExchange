# Facebook ThreatExchange

ThreatExchange is a set of RESTful APIs on the Facebook Platform for querying, publishing, and sharing security threat information. It's a lightweight way for exchanging details on malware, phishing pages, and other threats with either specific members of the community or the ThreatExchange community at large.

This repository contains example code for using the API.

## Documentation

Full details on the ThreatExchange API, data formats, and best practices are available in the [ThreatExchange docs](https://developers.facebook.com/docs/threat-exchange/).

## New tools for a new generation (2019 and beyond)

In addition to the venerable pytx (see below), we now offer tag-based, descriptor-focused reference designs in [**Python**](https://github.com/facebook/ThreatExchange/blob/master/hashing/te-tag-query-python), [**Ruby**](https://github.com/facebook/ThreatExchange/blob/master/hashing/te-tag-query-ruby), and [**Java**](https://github.com/facebook/ThreatExchange/blob/master/hashing/te-tag-query-java).

The common context to all these is that since early 2018 ThreatExchange has moved beyond malware/phishing into cross-company integrity-signal sharing. This newer tooling largely overlaps the old (such as pytx), but with an added focus on more interactive tooling for a broader, more diverse userbase; a strong threat-descriptor focus (vs malware analyses); and enhanced support for cross-company feedback mechanisms.

## Example code

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
