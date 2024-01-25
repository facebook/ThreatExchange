Instead of submitting to the HMA pipeline it is sometimes useful to see if an aggregate signal (e.g. a hash) would match result in a match if submitted and the context around the match. This functionality is provided through the `/matches/for-hash/` endpoint.

Request format: 
`GET` `<API ULR>/matches/for-hash/?signal_type=<signal_type>&signal_value=<signal_value>`

Current supported signal types: `pdq` & `video_md5`

Response:
`200` 

match found:

```sh
{
    "matches": [
        {
            "signal_id": "s-id",
            "privacy_group_id": "<pg-id",
            "signal_type": "pdq",
            "signal_hash": "<matched-hash>",
            "tags": [
                "test_pdq_samples"
            ]
        },
        ...
    ]
}
```
no match found:

```sh
{
    "matches": []
}
```

