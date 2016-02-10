# Facebook ThreatExchange

ThreatExchange is a set of RESTful APIs on the Facebook Platform for querying, publishing, and sharing security threat information. It's a light-weight way for exchanging details on malware, phishing pages, and other threats with either specific members of the community or the ThreatExchange community at large.

This repository contains example code for using the API.

## Documentation
Full details on the ThreatExchange API, data formats, and best practices are available at  [https://developers.facebook.com/docs/threat-exchange/](https://developers.facebook.com/docs/threat-exchange/)

## Example Code
This project offers example code in Python, PHP and Ruby.  There is also a reference user interface to ThreatExchanage, which is fully client-side, and written in Javascript!

## Get all available data

To get ALL the data in ThreatExchange, use our scripts in the get_all_data
folder. For example, to get all the threat indicators uploaded to ThreatExchange
over the last 10 days with the text "facebook", run the following command:

   $ python ./get_all_data/get_threat_indicators.py --text="facebook"
     --days_back=10

## Blog
You can get details on the ThreatExchange platform, new features and other updates via our blog at [https://www.facebook.com/threatexchange](https://www.facebook.com/threatexchange).

## Getting Access
To request access to ThreatExchange, please submit an application via [https://developers.facebook.com/products/threat-exchange/](https://developers.facebook.com/products/threat-exchange/).
