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

# Compiling the code

```
javac com/facebook/threatexchange/*.java
```

# Examples of using the code

On-line help:
```
java com.facebook.threatexchange.TETagQuery --help
```

Querying for all hashes of a given type:
```
java com.facebook.threatexchange.TETagQuery tag-to-details --indicator-type pdq media_type_photo

java com.facebook.threatexchange.TETagQuery -v tag-to-details --indicator-type pdq media_type_photo

java com.facebook.threatexchange.TETagQuery tag-to-details --indicator-type md5 media_type_video

java com.facebook.threatexchange.TETagQuery tag-to-details \
  --page-size 10 \
  --data-dir ./tmk-hash-dir \
  --indicator-type tmk \
  media_type_long_hash_video
```

Querying for some hashes of a given type:
```
java com.facebook.threatexchange.TETagQuery tag-to-details --indicator-type pdq --since -1day media_type_photo

java com.facebook.threatexchange.TETagQuery tag-to-details --indicator-type md5 --since -1week media_type_video

java com.facebook.threatexchange.TETagQuery tag-to-details \
  --page-size 10 \
  --data-dir ./tmk-hash-dir \
  --indicator-type tmk \
  --since -1week \
  media_type_long_hash_video
```

Post a new TMK hash:

```
java com.facebook.threatexchange.TETagQuery \
  submit \
    -i ../tmk/sample-hashes/chair-22-sd-sepia-bar.tmk \
    -t HASH_TMK \
    -d "testing te-tag-query with post" \
    -l AMBER \
    -s MALICIOUS \
    -p HAS_WHITELIST \
    --privacy-members 1064060413755420 \
    --tags testing_java_post
```

# Setup

* Find your app's access token at https://developers.facebook.com/tools/accesstoken/

* Put this into `~/.txtoken` and `chmod 600 ~/.txtoken`

* `export TX_ACCESS_TOKEN=$(cat ~/.txtoken)` in your shell's init file

# Contact

threatexchange@fb.com
