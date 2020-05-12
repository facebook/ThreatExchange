Example technique for retrieving hashes with a given tag from ThreatExchange, as well as uploading.

# Purpose of this code

You can use this for downloading/uploading hashes from/to ThreatExchange, found by tag. You can use the Ruby code as-is, or use it to illuminate tooling in other languages. Note that `te-tag-query-ruby -s ...` will print the URLs this tool constructs for you, to help make clear how to access ThreatExchange via URLs.

# Query mechanism

* We use the `tagged_objects` endpoint to fetch IDs of all hashes. This
endpoint doesn't return all desired metadata fields, so we use it as a quick
map from tag ID to list of hash IDs. This is relatively quick.

* Then for each resulting hash ID we do a query for all fields associated with
that ID. This is relatively slow, but batching multiple IDs per query helps a
lot.

# Contact

threatexchange@fb.com

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

# Bare-curl notes

As noted at the top of this document, the `TETagQuery` program is intended to be a reference design -- for you to use as-is, or to help you write tooling in other languages.

As noted above, the `TETagQuery` program uses a three-step process: tag text to tag ID; tag ID to tagged objects (with pagination); each page of tagged-object IDs to their details.

For reference, we show what those bare-curl commands look like if you're not using the Ruby code:

https://github.com/facebook/ThreatExchange/blob/master/hashing/te-tag-query-java/README.md
