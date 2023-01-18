# Copyright (c) Meta Platforms, Inc. and affiliates.

import json
import hmac
import typing as t
import requests

from dataclasses import dataclass

from hmalib.common.logging import get_logger


"""
When deployed correctly, this integration will 
 * process requests sent by a Workplace bot
 * athenticate that they came from the correct workplace bot
 * convert them to the form HMA expects
 * submit to HMA


How to ship this workplace integration using AWS:

1. In your workplace community create a bot/app
2. Give the bot permission to read from the necessary groups
3. Set WORKPLACE_APP_SECRET to be the secret from this bot
4. Set HMA_API_GATEWAY_URL to be the URL for the HMA API 
   (output when terraform apply is run)
5. Set HMA_API_TOKEN to be the authorization token used to 
   authenticate access to HMA API
6. Ship this as a lambda function in Aws. The easiest way to
   do that might be by adding it to terraform. The code in 
   examples/workplace.tf might be useful
7. Create a new API Gateway in AWS that points to this lambda
   function. You do not need to add an authenticator to the 
   path since this lambda will handle athenticating that the
   request truly came from your Workplace bot
8. Set up your workplace bot to send request to the new API 
   Gateway
9. Set up Actions and Action Rules in HMA as necessary

   An Action and Action rule to comment on the post with the 
   violating content for a match against dataset 12345 might 
   look like:

   ACTION:
      Name: WorkplaceCommentAction
      URL : https://graph.facebook.com/<content-id>/comments?message=Attention+Civilian!+This+post+violates+our+terms+of+service.+The+authorities+have+been+notified+and+they+are+on+the+way.+Good+Luck!
      Webhook Type : POST
      Headers : {"Authorization": "Bearer WORKPLACE-ACCESS-TOKEN", "User-Agent": "HMA"}

   ACTION RULE:
      Name: Comment On Workplace Matches
      Classification Conditions: 
         Dataset Source = te
         SubmittedContent has been classified = integration_source:workplace
      Action: WorkplaceCommentAction

   NOTE: 
   1. HMA will parse "<content-id>" and replace with the submitted
      content-id. This script stores uses WorkplacePostID as the 
      content-id.
   2. Replace WORKPLACE-ACCESS-TOKEN with the access token from your workplace bot
"""

logger = get_logger()

# Placeholder values
# You could optionally chose to deploy these as terraform variables
WORKPLACE_APP_SECRET = "1234567"
HMA_API_GATEWAY_URL = "https://xxxxxxxxx.execute-api.us-east-1.amazonaws.com"
HMA_API_TOKEN = "7654321"


@dataclass
class PhotoToUpload:
    photo_id: str
    photo_url: str
    additional_fields: t.List[str]


def lambda_handler(event, context):
    logger.info(event)

    if not can_process_request(event):
        logger.info("Cannot Process Request")
        return {"statusCode": 400, "body": json.dumps(event)}
    if not authorize_request(event):
        logger.info("Cannot Authorize Request")
        return {"statusCode": 400, "body": json.dumps("Cannot Authorize Request")}
    response, content_to_upload = process_request(event)
    for content in content_to_upload:
        print(f"Uploading content with ID {content.photo_id} to HMA")
        upload_to_HMA(content)

    return response


def upload_to_HMA(content: PhotoToUpload):
    submit_payload = {
        "content_id": content.photo_id,
        "content_type": "photo",
        "content_url": content.photo_url,
        "additional_fields": content.additional_fields,
        "force_resubmit": True,  # For testing, allow duplicate submission
    }

    payload_bytes = json.dumps(submit_payload).encode()

    response = requests.post(
        url=HMA_API_GATEWAY_URL + "/submit/url/",
        headers={
            "Content-Type": "application/json",
            "Authorization": HMA_API_TOKEN,
        },
        data=payload_bytes,
    )
    response.raise_for_status()

    logger.info(response.json())


def get_bytes_from_url(url: str):
    r = requests.get(url)
    r.raise_for_status()
    return r.content


def process_request(
    event: t.Dict[str, t.Any],
) -> t.Tuple[t.Any, t.List[PhotoToUpload]]:
    if "queryStringParameters" in event:
        query_params = event["queryStringParameters"]
        if "hub.challenge" in query_params:
            # This is used by Workplace to verify the webhook endpoint.
            # We must return the hub.challenge value back to them
            return (
                query_params["hub.challenge"],
                [],
            )

    body = json.loads(event["body"])
    submit_content_requests = []

    for entry in body["entry"]:
        for change in entry["changes"]:
            value: dict = change["value"]
            post_id = value["post_id"]
            post_text = value.get("message", "NO MESSAGE CONTENT")
            logger.info(f'Found an post that says: "{post_text}"')
            if "attachments" in value:
                for attachment in value["attachments"]["data"]:
                    if attachment["type"] == "photo":
                        photo_id: str = attachment["target"]["id"]
                        photo_url: str = attachment["media"]["image"]["src"]
                        logger.info(
                            f"Found an image with ID {photo_id} and URL {photo_url}"
                        )
                        submit_content_requests.append(
                            PhotoToUpload(
                                # Super Hacky workaround. We use the post id as the content id
                                # so that we can include it in the action using replacement.
                                # We will want to eventually enable action replacement to support
                                # additional fields. For now, though, this means that if a workplace
                                # post reaches HMA which has multiple image attachements, only one
                                # image will be processed by HMA.
                                post_id,
                                photo_url,
                                [
                                    "integration_source:workplace",
                                    f"post_id:{post_id}",
                                    f"post_text:{post_text}",
                                ],
                            )
                        )
            else:
                logger.info(f"No images to process on post")

    # Workplace doesnt need a response to webhooks
    response = None

    return (response, submit_content_requests)


def authorize_request(
    event: t.Dict[str, t.Any],
) -> bool:
    # Follow webhook implementation here to confirm request came from workplace
    # https://facebook-pybot.readthedocs.io/en/dev/_modules/Facebook/webhook.html
    body = event["body"].encode("utf-8")
    secret = WORKPLACE_APP_SECRET.encode("utf-8")
    hmac_object = hmac.new(secret, body, "sha1")
    expected_sha = hmac_object.hexdigest()
    _, provided_sha = event["headers"]["x-hub-signature"].split("=")
    return hmac.compare_digest(provided_sha, expected_sha)


def can_process_request(
    event: t.Dict[str, t.Any],
) -> bool:
    return (
        "queryStringParameters" in event
        and "hub.verify_token" in event["queryStringParameters"]
    ) or has_workplace_body(event)


def has_workplace_body(
    event: t.Dict[str, t.Any],
) -> bool:
    if "body" not in event:
        return False
    if "headers" not in event:
        return False
    body = json.loads(event["body"])
    return "entry" in body and body["entry"] and "changes" in body["entry"][0]


if __name__ == "__main__":
    event = {
        "version": "2.0",
        "routeKey": "POST /submit/integration",
        "rawPath": "/submit/integration",
        "rawQueryString": "",
        "headers": {
            "accept": "*/*",
            "content-length": "537",
            "content-type": "application/json",
            "host": "wvc66cfkp4.execute-api.us-east-1.amazonaws.com",
            "user-agent": "Webhooks/1.0 (https://fb.me/webhooks)",
            "x-amzn-trace-id": "Root=1-612d5821-475c90390187f87e37222a84",
            "x-forwarded-for": "69.171.251.1",
            "x-forwarded-port": "443",
            "x-forwarded-proto": "https",
            "x-hub-signature": "sha1=ad2ba62e9e251f70a8eef74f608e6d2b1bf578f1",
        },
        "requestContext": {
            "accountId": "521978645842",
            "apiId": "wvc66cfkp4",
            "domainName": "wvc66cfkp4.execute-api.us-east-1.amazonaws.com",
            "domainPrefix": "wvc66cfkp4",
            "http": {
                "method": "POST",
                "path": "/submit/integration",
                "protocol": "HTTP/1.1",
                "sourceIp": "69.171.251.1",
                "userAgent": "Webhooks/1.0 (https://fb.me/webhooks)",
            },
            "requestId": "E5q1Tjc2oAMESBQ=",
            "routeKey": "POST /submit/integration",
            "stage": "$default",
            "time": "30/Aug/2021:22:13:53 +0000",
            "timeEpoch": 1630361633774,
        },
        "body": '{"object": "group", "entry": [{"id": "320351789823264", "time": 1630361633, "changes": [{"value": {"created_time": "2021-08-30T22:13:50+0000", "comment_id": "341469824378127", "community": {"id": "793780977425128"}, "from": {"id": "100052969254292", "name": "David Callies"}, "message": "Woah, look at those rotations!", "post_id": "320351789823264_341450157713427", "permalink_url": "https://threatexchange.workplace.com/groups/320351789823264/posts/341450157713427/?comment_id=341469824378127", "verb": "add"}, "field": "comments"}]}]}',
        "isBase64Encoded": False,
    }
    print(lambda_handler(event, None))
