The Content Submissions API allows you to send [Content](Glossary#content) from your platform to be ingested into the HMA system.

Since HMA can't see into your platform, it will use your own platform's content ID schema for deduplication and logging, and the resultant actions from content evaluation will include the content ID (as well as any `additional_fields` you've added at submission time). As long as you upload the same content with the same parameters, the API is idempotent (given no other state changes). Re-using the same id for different submission endpoints or parameters results in undefined behavior.

See Also:
The [Submit Content UI page](Submit-Content) that calls this API.

## The Submission API has 4 endpoints

### Common fields

All submission endpoints have 4 common fields/parameters (two always required and two optional):

- Parameters:
  - `content_id` (string)
    - your platform's id for this content
  - `content_type` (string, one of):
    - `photo`
    - `video`
  - `additional_fields` (optional list of strings)
    - Added to as metadata on the Content
  - `force_resubmit` (optional boolean [default=False])
    - flag that must be set to true for successful submission with `content_id` already found in system


### 1) Submitting a URL to content

- Endpoint:
  - `/submit/url/`
- Endpoint specific parameters:
  - `content_url`
    URL to send a get request for content media
- Response
  - `Status: 200 OK` - The content was successfully ingested into HMA
  - `Status: 400 Bad Request` - One of the parameters had an issue - see the returned message
- Notes:
  - Does not store a copy of the content. The hashing function requests the bytes and only records hash and metadata.

### 2) Submitting bytes of content directly

- Endpoint:
  - `/submit/bytes/`
- Endpoint specific parameters:
  - `content_bytes`
    - bytes (64bit encode) for of an image which is decoded and copied to s3
- Response
  - `Status: 200 OK` - The content was successfully ingested into HMA
  - `Status: 400 Bad Request` - One of the parameters had an issue - see the returned message
- Notes:
  - Request size limitation result in images greater than 3.5MB being likely to fail.

### 3) Submitting a hash of content

- Endpoint:
  - `/submit/hash/`
- Endpoint specific parameters:
  - `signal_value` (string)
    - Hash of the content corresponding to `content_id`
  - `signal_type` (string, one of):
    - `pdq`
    - `video_md5`
  - `content_url` (optional)
    URL to content media corresponding to hash
- Response
  - `Status: 200 OK` - The content ('s hash) was successfully ingested into HMA
  - `Status: 400 Bad Request` - One of the parameters had an issue - see the returned message
- Notes:
  - This submission endpoint is a two step process for the client. The initial request creates the content record and post_url given in response.
  - The second request uses the given URL to upload the content media.  

### 4) Submitting via returned put url

- Endpoint:
  - `/submit/put-url/`
- Endpoint specific parameters:
  - `file_type`
    - type of file the client wishes to upload directly to s3. Used to create and return signed url
- Response
  - `Status: 200 OK` - The content was successfully ingested into HMA
    - response contains presigned_url allowing client to upload corresponding file to HMA's s3 storage
  - `Status: 400 Bad Request` - One of the parameters had an issue - see the returned message
- Notes:
  - This submission endpoint is a two step process for the client. The initial request creates the content record and post_url given in response.
  - The second request uses the given URL to upload the content media.  

## Examples

In cases where the status is not 200, a payload with more context is returned.

```json
{
  "message": "error"
}
```

The payload of the response depends endpoint:

`/submit/bytes/` & `/submit/url/` & `/submit/hash/`

```json
{
  "content_id": "12345",
  "submit_successful": "True"
}
```

`/submit/put-url/`

```json
{
  "content_id": "12345",
  "file_type": "image/jpeg",
  "presigned_url": "www.example.com"
}
```
