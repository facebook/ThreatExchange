Here's a super-rough first cut for an API

# Match a new hash against the index

```
GET /v1/hashes/?hash=<PDQ-hash-in-hex>
{
  "hash": "<PDQ Hash>"
}
```

`200 OK` with following shape if found, `404 Not Found` if not.

```
{
  "hash": "<PDQ Hash as string>"
}
```
