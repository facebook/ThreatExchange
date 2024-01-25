Beyond using the [Submit Content Page](Submit-Content) to submit to HMA. The [Submit API](Content-Submissions-API) can be used to submit [Content](Glossary#hasher) to the system. See [How does your media flow through the HMA?](How-does-your-media-flow-through-HMA?) for details on what happens to your data next.

To walk through this tutorial you need to have [successfully deployed HMA](Installation) and [gotten access to to the system](Granting-access-to-more-users).

Examples
-----------
Content is submitted to the system via a POST HTTP request. The following are code example in python that submit an image to the system:

For these python examples...

* The deployed system and associated api can be reached at `https://abcd1234.execute-api.us-east-1.amazonaws.com/`
* The content want to submit can be found on at `/path/to/file`
    * or via the url `https://presigned-url-to-the-image.xyz/abc`

* The Content is an image of type `jpeg`
* `API_TOKEN` is an freshly authenticated access token.


#### Example 1: UPLOAD - Submit in 2 phases. First request gets a url to send the content data (handles larger images)
```python
import requests
import json

submit_payload = {
    "content_id": "unqiue_identifier_for_content_1",
    "content_type": "photo",
    "file_type": "image/jpeg",  # file_type to allow system to build upload url
    "additional_fields": [
        "source:programatic_upload_example1",
        "optional_record:value2",
    ],
}

payload_bytes = json.dumps(submit_payload).encode()

response_json = requests.post(
    url="https://abcd1234.execute-api.us-east-1.amazonaws.com/submit/put-url/",
    headers={
        "Content-Type": "application/json",
        "Authorization": API_TOKEN,
    },
    data=payload_bytes,
).json()

with open("/path/to/file", "rb") as file:
    put_response = requests.put(
        response_json["presigned_url"],
        data=file,
        headers={"content-type": "image/jpeg"},
    )
```


#### Example 2: from a URL -  provide a url to the image had have the system send a get request
```python
import requests
import json

submit_payload = {
    "content_id": "unqiue_identifier_for_content_2",
    "content_type": "photo",
    "content_url": "https://presigned-url-to-the-image.xyz/abc",  # url to image
    "additional_fields": [
        "source:programatic_upload_example2",
        "optional_record:value2",
    ],
}

payload_bytes = json.dumps(submit_payload).encode()

requests.post(
    url="https://abcd1234.execute-api.us-east-1.amazonaws.com/submit/url/",
    headers={
        "Content-Type": "application/json",
        "Authorization": API_TOKEN,
    },
    data=payload_bytes,
)
```

This code snippets could be used in part of a content pipeline to submits images to HMA.

