Here's a super-rough first cut for an API

# Match a single hash against the index

```
GET /v1/hashes/query?hash=hash_in_hex_string
```

`200 OK` if found, `404 Not Found` if not.

# Match multiple hashes against the index

```
POST /v1/hashes/query
{
    "hashes": [
        ...hashes in hex string
    ]
}
```

`200 OK` with following shape.

```
{
  "matched_hashes": ["hash1 in hex string", "hash2 in hex string"],
  "unmatched_hashes": ["hash3 in hex string", "hash4 in hex string"],
}
```
