Example technique for retrieving hashes with a given tag from ThreatExchange, as well as uploading.

# Purpose of this code

You can use this for downloading/uploading hashes from/to ThreatExchange, found by tag. You can use the Java code as-is, or use it to illuminate tooling in other languages. Note that `java TETagQuery -s ...` will print the URLs this tool constructs for you, to help make clear how to access ThreatExchange via URLs.

# Query mechanism

* We use the `tagged_objects` endpoint to fetch IDs of all hashes. This
endpoint doesn't return all desired metadata fields, so we use it as a quick
map from tag ID to list of hash IDs. This is relatively quick.

* Then for each resulting hash ID we do a query for all fields associated with
that ID. This is relatively slow, but batching multiple IDs per query helps a
lot.

# Contact

threatexchange@meta.com

# Compiling the code

```
javac com/facebook/threatexchange/*.java
```

# Running the code

The `te-tag-query-java` wrapper script sets the Java classpath and invokes the main Java method in `com/facebook/threatexchange/TETagQuery.java`.

# Setup

* Find your app's access token at https://developers.facebook.com/tools/accesstoken/

* Put this into `~/.txtoken` and `chmod 600 ~/.txtoken`

* `export TX_ACCESS_TOKEN=$(cat ~/.txtoken)` in your shell's init file

# Examples of using the code for queries

On-line help:
```
te-tag-query-java --help
```

Querying for all hashes of a given type:
```
te-tag-query-java tag-to-details --indicator-type pdq media_type_photo

te-tag-query-java -v tag-to-details --indicator-type pdq media_type_photo

te-tag-query-java tag-to-details --indicator-type md5 media_type_video

te-tag-query-java tag-to-details \
  --page-size 10 \
  --data-dir ./tmk-data-dir \
  --indicator-type tmk \
  media_type_long_hash_video
```

Querying for some hashes of a given type:
```
te-tag-query-java tag-to-details --indicator-type pdq --tagged-since -1day media_type_photo

te-tag-query-java tag-to-details --indicator-type md5 --tagged-since -1week media_type_video

te-tag-query-java tag-to-details \
  --page-size 10 \
  --data-dir ./tmk-data-dir \
  --indicator-type tmk \
  --tagged-since -1week \
  media_type_long_hash_video
```

# Examples of using the code for posts

Post a new SHA1 hash:

```
te-tag-query-java submit \
  -i dabbad00f00dfeed5ca1ab1ebeefca11ab1ec00e \
  -t HASH_SHA1 \
  -d "testing te-tag-query with post" \
  -l AMBER \
  -s NON_MALICIOUS \
  -p HAS_WHITELIST \
  --privacy-members 1064060413755420 \
  --tags testing_java_post
```

Suppose that prints `{"success":true,"id":"2964083130339380"}`.

Update it, using that ID:

```
te-tag-query-java update \
  -i 2964083130339380 \
  -s UNKNOWN \
  --add-tags testing_java_update
```

Post another with relation to the first one:

```
te-tag-query-java submit \
  -i dabbad00f00dfeed5ca1ab1ebeefca11ab1ec00f \
  -t HASH_SHA1 \
  -d "testing te-tag-query with post" \
  -l AMBER \
  -s NON_MALICIOUS \
  -p HAS_WHITELIST \
  --privacy-members 1064060413755420 \
  --tags testing_java_post \
  --related-triples-for-upload-as-json '[{"owner_app_id":494491891138576,"td_indicator_type":"HASH_SHA1","td_raw_indicator":"dabbad00f00dfeed5ca1ab1ebeefca11ab1ec00e"}]'
```

Make copies of a set of descriptors, e.g. from a data-sharing partner:

```
$ jq '.id | tonumber' partner-data.json
1791017857689049
3061881580561662
3186579388076637
2927363690632863
4036655176350945
2920637101389201
2519477894818399
```

Here you copy all descriptor data from the query output, only modifying your own values.
Note, however, that for the present you must explicitly set `--privacy-members`.

```
$ jq '.id | tonumber' partner-data.json \
| te-tag-query-java copy -N \
  --description 'our copies' \
  --privacy-type HAS_PRIVACY_GROUP --privacy-members 781588512307315
{"success":true,"id":"1791017857689049"}
{"success":true,"id":"3061881580561662"}
{"success":true,"id":"3186579388076637"}
{"success":true,"id":"2927363690632863"}
{"success":true,"id":"4036655176350945"}
{"success":true,"id":"2920637101389201"}
{"success":true,"id":"2519477894818399"}
```

```
$ te-tag-query-java ids-to-details 1791017857689049 | jq .
{
  "id": "1791017857689049",
  "td_raw_indicator": "dabbad00f00dfeed5ca1ab1ebeefca11ab1ec0cf",
  "td_indicator_type": "HASH_SHA1",
  "added_on": "2020-07-02T19:56:05+0000",
  "last_updated": "2020-07-02T21:08:31+0000",
  "td_confidence": "100",
  "td_owner_id": "494491891138576",
  "td_owner_email": "threatexchange@meta.com",
  "td_owner_name": "Media Hash Sharing RF Test",
  "td_visibility": "HAS_PRIVACY_GROUP",
  "td_review_status": "REVIEWED_AUTOMATICALLY",
  "td_status": "NON_MALICIOUS",
  "td_severity": "INFO",
  "td_share_level": "AMBER",
  "td_subjective_tags": "pwny,testing",
  "td_description": "our copies"
}
```

Post a new TMK hash:

```
te-tag-query-java \
  submit \
    -i ../tmk/sample-hashes/chair-22-sd-sepia-bar.tmk \
    -t HASH_TMK \
    -d "testing te-tag-query with post" \
    -l AMBER \
    -s NON_MALICIOUS \
    -p HAS_WHITELIST \
    --privacy-members 1064060413755420 \
    --tags testing_java_post
```

# Examples of using the API wrappers

The above examples use the `te-tag-query-java` script. However, if you'd like more easily copyable examples of using the API, you can look at `APIExamples.java` in the current directory.

# Bare-curl notes

As noted at the top of this document, the `TETagQuery` program is intended to be a reference design -- for you to use as-is, or to help you write tooling in other languages.

For reference, we show what those bare-curl commands look like if you're not using the Java code:

https://github.com/facebook/ThreatExchange/blob/main/hashing/te-tag-query-curl/README.md

The HTTP queries shown there were generated by running `TETagQuery -s ...`; those URLs were dropped into a browser to obtain the raw JSON responses shown there.
