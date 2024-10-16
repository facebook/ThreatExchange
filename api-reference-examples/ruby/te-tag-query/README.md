Example technique for retrieving hashes with a given tag from ThreatExchange, as well as uploading.

# Purpose of this code

You can use this for downloading/uploading hashes from/to ThreatExchange, found by tag. You can use the Ruby code as-is, or use it to illuminate tooling in other languages. Note that `te-tag-query-ruby -s ...` will print the URLs this tool constructs for you, to help make clear how to access ThreatExchange via URLs.

# Dependencies

Ruby standard libraries. Tested on Ruby 2.6.

# Query mechanism

* We use the `tagged_objects` endpoint to fetch IDs of all hashes. This
endpoint doesn't return all desired metadata fields, so we use it as a quick
map from tag ID to list of hash IDs. This is relatively quick.

* Then for each resulting hash ID we do a query for all fields associated with
that ID. This is relatively slow, but batching multiple IDs per query helps a
lot.

# Contact

threatexchange@meta.com

# Files

There are three.

1. The `te-tag-query-ruby` wrapper script sets the Ruby path and invokes the main Ruby method in `TETagQuery.rb`.

```
#!/bin/bash
ourdir=`dirname $0`
# Set up the Ruby path so this Ruby program can be invoked from anywhere.
exec ruby -I $ourdir $ourdir/TETagQuery.rb "$@"
```

2. `TETagQuery.rb` contains command-line parsing and invokes the library methods in `TENet.rb`.

3. `TENet.rb` contains the library methods.

# Setup

* Find your app's access token at https://developers.facebook.com/tools/accesstoken/

* Put this into `~/.txtoken` and `chmod 600 ~/.txtoken`

* `export TX_ACCESS_TOKEN=$(cat ~/.txtoken)` in your shell's init file

# Examples of using the code for queries

On-line help:
```
te-tag-query-ruby --help
```

Querying for all hashes of a given type:
```
te-tag-query-ruby tag-to-details media_type_photo

te-tag-query-ruby -v tag-to-details media_type_photo

te-tag-query-ruby tag-to-details media_type_video
```

Querying for some hashes of a given type:
```
te-tag-query-ruby tag-to-details --tagged-since -1day media_type_photo

te-tag-query-ruby tag-to-details --tagged-since -1week media_type_video
```

# Examples of using the code for posts

Post a new SHA1 hash:

```
te-tag-query-ruby submit \
  -i dabbad00f00dfeed5ca1ab1ebeefca11ab1ec10e \
  -t HASH_SHA1 \
  -d "testing te-tag-query with post" \
  -l AMBER \
  -s NON_MALICIOUS \
  -p HAS_WHITELIST \
  --privacy-members 1064060413755420 \
  --tags testing_ruby_post
```

Suppose that prints `{"success":true,"id":"3546989395318416"}`.

Update it, using that ID:

```
te-tag-query-ruby update \
  -i 3546989395318416 \
  -s UNKNOWN \
  --add-tags testing_ruby_update
```

React to another app's descriptor:

```
te-tag-query-ruby update -n 2589692907727086 --reactions-to-add INGESTED,IN_REVIEW
{"success": true}
```

Post another with relation to the first one:

```
te-tag-query-ruby submit \
  -i dabbad00f00dfeed5ca1ab1ebeefca11ab1ec10f \
  -t HASH_SHA1 \
  -d "testing te-tag-query with post" \
  -l AMBER \
  -s NON_MALICIOUS \
  -p HAS_WHITELIST \
  --privacy-members 1064060413755420 \
  --tags testing_ruby_post \
  --related-triples-for-upload-as-json '[{"owner_app_id":494491891138576,"td_indicator_type":"HASH_SHA1","td_raw_indicator":"dabbad00f00dfeed5ca1ab1ebeefca11ab1ec10e"}]'
```

Make copies of a set of descriptors, e.g. from a data-sharing partner:

```
$ jq '.id | tonumber' partner-data.json
1548810399019426
1638880316185816
1934838869863501
1508037889310099
1560856918869301
1590064801887298
1661005877388540
1670668732978808
1788683904488807
1811154288888224
```

Here you copy all descriptor data from the query output, only modifying your own values.
Note, however, that for the present you must explicitly set `--privacy-members`.

```
$ jq '.id | tonumber' partner-data.json \
| te-tag-query-ruby copy -N \
  --description 'our copies' \
  --privacy-type HAS_PRIVACY_GROUP --privacy-members 781588512307315
{"success":true,"id":"3216884688390703"}
{"success":true,"id":"3039118856170891"}
{"success":true,"id":"3049939888083721"}
{"success":true,"id":"3180176808832725"}
{"success":true,"id":"3280047872888160"}
{"success":true,"id":"3415103841888795"}
{"success":true,"id":"2912237555558894"}
{"success":true,"id":"4163069720400887"}
{"success":true,"id":"3080705925329880"}
{"success":true,"id":"3046896738736542"}
```

```
$ te-tag-query-ruby ids-to-details 3046896738736542 | jq .
{
  "raw_indicator": "c7dfd847207cbd54a8bb292525fc111d",
  "type": "HASH_MD5",
  "added_on": "2020-06-03T01:38:01+0000",
  "last_updated": "2020-06-03T01:38:02+0000",
  "confidence": 100,
  "owner": {
    "id": "494491891138576",
    "email": "threatexchange@meta.com",
    "name": "Media Hash Sharing RF Test"
  },
  "privacy_type": "HAS_PRIVACY_GROUP",
  "review_status": "REVIEWED_AUTOMATICALLY",
  "status": "MALICIOUS",
  "severity": "WARNING",
  "share_level": "AMBER",
  "description": "our copies",
  "id": "3046896738736542",
  "tags": []
}
```

# Examples of using the API wrappers

The above examples use the `te-tag-query-ruby` script. However, if you'd like more easily copyable examples of using the API, you can do

```
ruby api-example-submit.rb
ruby api-example-update.rb
ruby api-example-copy.rb
```

# Bare-curl notes

As noted at the top of this document, the `TETagQuery` program is intended to be a reference design -- for you to use as-is, or to help you write tooling in other languages.

For reference, we show what those bare-curl commands look like if you're not using the Ruby code:

https://github.com/facebook/ThreatExchange/blob/main/hashing/te-tag-query-curl/README.md
