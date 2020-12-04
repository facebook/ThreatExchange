# python-threatexchange

A Python Library for downloading and using datasets stored in ThreatExchange.

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Overview
Fetching data from ThreatExchange "correcty" is sadly not as straightforward as it should be.

Additionally, once you have the data, the application of that data might not always be straightforward.

This library provides a reference implementation for fetching datasets, applying many common formats, and uploading your own data to the dataset.

These reference implementations are not meant to be the best, most efficient, or production ready versions, but to instead be simple enough that they could be easily pasted to other languages. 

The bundled cli tool of the same name is meant to demonstrate the library, as well as potentially provide a first draft implementation for prototype or evaluation. 

## Installation

```bash
$ python3 -m pip install threatexchange [--upgrade]
```

## Usage
This package can be used as a library, but the fastest way to use it is from the CLI

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


## Documentation
The best documentation is in the --help of the tool, as well as the docstrings in libraries. Open issues if something is lacking.
