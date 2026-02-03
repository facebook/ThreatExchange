Example technique for retrieving hashes with a given tag from ThreatExchange, as well as uploading.

# Purpose of this code

You can use this for downloading/uploading hashes from/to ThreatExchange, found by tag. You can use the code as-is, or use it to illuminate tooling in other languages.

Construting URLs by hand is tedious and error-prone; hence we recommend

* https://github.com/facebook/ThreatExchange/blob/main/hashing/te-tag-query-java
* https://github.com/facebook/ThreatExchange/blob/main/hashing/te-tag-query-ruby

Nonetheless, for those wanting to use curls directly, the URLs in this document were prepared using the `-s` output from the Java reference design, and those URLs were dropped into a browser to obtain the raw JSON responses shown below.

See also https://developers.facebook.com/docs/threat-exchange/reference/apis

# Query mechanism

* We use the `tagged_objects` endpoint to fetch IDs of all hashes. This
endpoint doesn't return all desired metadata fields, so we use it as a quick
map from tag ID to list of hash IDs. This is relatively quick.

* Then for each resulting hash ID we do a query for all fields associated with
that ID. This is relatively slow, but batching multiple IDs per query helps a
lot.

# Contact

threatexchange@meta.com

# Setup

* Find your app's access token at https://developers.facebook.com/tools/accesstoken/
* Put this into `~/.txtoken` and `chmod 600 ~/.txtoken`
* `export TX_ACCESS_TOKEN=$(cat ~/.txtoken)` in your shell's init file

# Three-step paginated query

## Step 1: tag text to tag ID

HTTP query:

```
curl -s 'https://graph.facebook.com/v4.0/threat_tags/'\
"?access_token=$TX_ACCESS_TOKEN"\
'&text=pwny&limit=10'
```

JSON response:

```
{
   "data": [
      {
         "id": "2722789434440042",
         "text": "pwny2"
      },
      {
         "id": "1283621968426798",
         "text": "pwny"
      }
   ],
   "paging": {
      "cursors": {
         "before": "MAZDZD",
         "after": "MQZDZD"
      }
   }
}
```

This does a prefix-match so select and retain the ID for the exact match `pwny`.

## Step 2: tag ID to tagged-object IDs

HTTP query:

```
curl -s 'https://graph.facebook.com/v4.0/1283621968426798/tagged_objects/'\
"?access_token=$TX_ACCESS_TOKEN"\
'&limit=100'
```

JSON response:

```
{
   "data": [
      {
         "id": "2556006484495859",
         "type": "THREAT_DESCRIPTOR",
         "name": "ginuwine1551474919abc-2.evilevillabs.com"
      },
      {
         "id": "2356527701137016",
         "type": "THREAT_DESCRIPTOR",
         "name": "e8b19da37825a3056e84c522f05ee081"
      },
      ...
  ],
  "paging": {
    "cursors": {
      "before": "REDACTED",
      "after": "REDACTED"
    },
   "next": "https://graph.facebook.com/v6.0/2733125556794397/tagged_objects?access_token=REDACTED&limit=1000&after=..."
  }
}
```

If there is no next page the `response.paging.next` will be absent. If it is present, you can simply curl it as-is to follow the next page, and the next, until there are no more.

## Step 3: tagged-object IDs to descriptor details

Here we collect the IDs from the above single-page JSON response and get details for each of them.

HTTP query:

```
curl -s 'https://graph.facebook.com/v4.0/'\
"?access_token=$TX_ACCESS_TOKEN"\
'&ids=%5B2556006484495859,2356527701137016%5D'\
'&fields=raw_indicator,type,added_on,last_updated,confidence,owner,privacy_type,review_status,status,severity,share_level,tags,description'
```

JSON response:

```
{
   "2556006484495859": {
      "raw_indicator": "ginuwine1551474919abc-2.evilevillabs.com",
      "type": "DOMAIN",
      "added_on": "2019-11-09T02:58:41+0000",
      "last_updated": "2019-11-09T02:58:42+0000",
      "confidence": 80,
      "owner": {
         "id": "494491891138576",
         "email": "redacted@redacted.com",
         "name": "Media Hash Sharing RF Test"
      },
      "privacy_type": "HAS_PRIVACY_GROUP",
      "review_status": "REVIEWED_MANUALLY",
      "status": "UNKNOWN",
      "severity": "INFO",
      "share_level": "AMBER",
      "tags": {
         "data": [
            {
               "id": "1283621968426798",
               "text": "pwny"
            },
            {
               "id": "1928945133884049",
               "text": "ignore"
            },
            {
               "id": "884078131700721",
               "text": "testing"
            }
         ]
      },
      "description": "Testing camel-casing codemod",
      "id": "2556006484495859"
   },
  ...
}
```

Here there is no next page since the details are from a list of IDs specified in the HTTP query.

# Submit a new threat descriptor

Here we post to the `threat_descriptors` endpoint.

See also https://developers.facebook.com/docs/threat-exchange/reference/submitting

HTTP query for post:

```
curl -s -X POST \
'https://graph.facebook.com/v4.0/threat_descriptors/'\
"?access_token=$TX_ACCESS_TOKEN"\
'&type=HASH_SHA1'\
'&description=API+testing'\
'&share_level=AMBER'\
'&status=NON_MALICIOUS'\
'&privacy_type=HAS_WHITELIST'\
'&privacy_members=1064060413755420'\
'&tags=testing_java_post'\
'&indicator=85fc2d2a3764089191e57cd55260127800005c46'
```

JSON response:

```
{"success":true,"id":"3047058802049882"}
```

HTTP query for read-back:

```
curl -s \
'https://graph.facebook.com/v4.0/'\
"?access_token=$TX_ACCESS_TOKEN"\
'&ids=%5B3047058802049882%5D'\
'&fields=raw_indicator,type,added_on,last_updated,confidence,owner,privacy_type,review_status,status,severity,share_level,tags,description'
```

JSON response for read-back:

```
{
  "3047058802049882": {
    "raw_indicator": "85fc2d2a3764089191e57cd55260127800005c46",
    "type": "HASH_SHA1",
    "added_on": "2020-05-12T16:38:37+0000",
    "last_updated": "2020-05-12T17:41:16+0000",
    "confidence": 50,
    "owner": {
      "id": "494491891138576",
      "email": "redacted@redacted.com",
      "name": "Media Hash Sharing RF Test"
    },
    "privacy_type": "HAS_WHITELIST",
    "review_status": "UNREVIEWED",
    "status": "NON_MALICIOUS",
    "severity": "INFO",
    "share_level": "AMBER",
    "tags": {
      "data": [
        {
          "id": "2911371008904239",
          "text": "testing_java_post"
        }
      ]
    },
    "description": "API testing",
    "id": "3047058802049882"
  }
}
```

# Edit an existing threat descriptor

Here we post to a `threat_descriptor` endpoint which is spelled, not
`threat_descriptor`, but instead simply using the ID of our just-created
descriptor from the previous example.

See also https://developers.facebook.com/docs/threat-exchange/reference/editing

HTTP query:

```
curl -s -X POST \
'https://graph.facebook.com/v4.0/3047058802049882/'\
"?access_token=$TX_ACCESS_TOKEN"\
'&description=Updating+description'
```

JSON response:

```
{"success":true}
```

HTTP query for read-back:

```
curl -s \
'https://graph.facebook.com/v4.0/'\
"?access_token=$TX_ACCESS_TOKEN"\
'&ids=%5B3047058802049882%5D'\
'&fields=raw_indicator,type,added_on,last_updated,confidence,owner,privacy_type,review_status,status,severity,share_level,tags,description'
```

JSON response for read-back:

```
{
  "3047058802049882": {
    "raw_indicator": "85fc2d2a3764089191e57cd55260127800005c46",
    "type": "HASH_SHA1",
    "added_on": "2020-05-12T16:38:37+0000",
    "last_updated": "2020-05-12T17:41:53+0000",
    "confidence": 50,
    "owner": {
      "id": "494491891138576",
      "email": "redacted@redacted.com",
      "name": "Media Hash Sharing RF Test"
    },
    "privacy_type": "HAS_WHITELIST",
    "review_status": "UNREVIEWED",
    "status": "NON_MALICIOUS",
    "severity": "INFO",
    "share_level": "AMBER",
    "tags": {
      "data": [
        {
          "id": "2911371008904239",
          "text": "testing_java_post"
        }
      ]
    },
    "description": "Updating description",
    "id": "3047058802049882"
  }
}
```

React to another app's descriptor:

```
curl -s -X POST \
'https://graph.facebook.com/v6.0/2589692907727086/'\
"?access_token=$TX_ACCESS_TOKEN"\
'&reactions=HELPFUL,SAW_THIS_TOO' \
| jq .

{
  "success": true
}
```
