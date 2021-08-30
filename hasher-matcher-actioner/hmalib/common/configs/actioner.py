# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import hmalib.common.config as config
import json
import typing as t

from dataclasses import dataclass
from hmalib.common.logging import get_logger
from hmalib.common.messages.match import BankedSignal, MatchMessage
from hmalib.common.aws_dataclass import HasAWSSerialization
from requests import get, post, put, delete, Response

logger = get_logger(__name__)


TUrl = t.Union[t.Text, bytes]


class ActionPerformer(config.HMAConfigWithSubtypes, HasAWSSerialization):
    """
    An ActionPerfomer is the configuration + the code to perform an action.

    All actions share the same namespace (so that a post action and a
    "send to review" action can't both be called "IActionReview")

    ActionPerformer.get("action_name").perform_action(match_message)
    """

    @staticmethod
    def get_subtype_classes():
        return [
            WebhookPostActionPerformer,
            WebhookGetActionPerformer,
            WebhookPutActionPerformer,
            WebhookDeleteActionPerformer,
        ]

    # Implemented by subtypes
    def perform_action(self, match_message: MatchMessage) -> None:
        raise NotImplementedError


# at match time, these strings are replaced by the result of running the associated
# function on the match message
WEBHOOK_ACTION_PERFORMER_REPLACEMENTS: t.Dict[str, t.Callable[[MatchMessage], str]] = {
    "<content-id>": lambda match_message: match_message.content_key,
    "<content-hash>": lambda match_message: match_message.content_hash,
}


@dataclass
class WebhookActionPerformer(ActionPerformer):
    """Superclass for webhooks"""

    url: str
    headers: str

    def perform_action(self, match_message: MatchMessage) -> None:
        parsed_url, parsed_headers = self.url, self.headers
        for (
            replacement_str,
            replacement_func,
        ) in WEBHOOK_ACTION_PERFORMER_REPLACEMENTS.items():
            parsed_url = parsed_url.replace(
                replacement_str, replacement_func(match_message)
            )
            parsed_headers = parsed_headers.replace(
                replacement_str, replacement_func(match_message)
            )
        self.call(parsed_url, parsed_headers, data=json.dumps(match_message.to_aws()))

    def call(self, url: str, headers: str, data: str) -> Response:
        raise NotImplementedError()


@dataclass
class WebhookPostActionPerformer(WebhookActionPerformer):
    """Hit an arbitrary endpoint with a POST"""

    def call(self, url: str, headers: str, data: str) -> Response:
        logger.info(f"Performing a POST request to URL. {self.url}")
        return post(url, data, headers=json.loads(headers))


@dataclass
class WebhookGetActionPerformer(WebhookActionPerformer):
    """Hit an arbitrary endpoint with a GET"""

    def call(self, url: str, headers: str, data: str) -> Response:
        logger.info(f"Performing a GET request to URL. {self.url}")
        return get(url, data, headers=json.loads(headers))


@dataclass
class WebhookPutActionPerformer(WebhookActionPerformer):
    """Hit an arbitrary endpoint with a PUT"""

    def call(self, url: str, headers: str, data: str) -> Response:
        logger.info(f"Performing a PUT request to URL. {self.url}")
        return put(url, data, headers=json.loads(headers))


@dataclass
class WebhookDeleteActionPerformer(WebhookActionPerformer):
    """Hit an arbitrary endpoint with a DELETE"""

    def call(self, url: str, headers: str, _data: str) -> Response:
        logger.info(f"Performing a DELETE request to URL. {self.url}")
        return delete(url, headers=json.loads(headers))


if __name__ == "__main__":
    content_id = "cid1"
    content_hash = "0374f1g34f12g34f8"

    banked_signal = BankedSignal(
        banked_content_id="4169895076385542",
        bank_id="303636684709969",
        bank_source="te",
    )

    action_performer = WebhookPostActionPerformer(
        name="EnqueueForReview",
        url="https://webhook.site/d0dbb19d-2a6f-40be-ad4d-fa9c8b34c8df",
        headers='{"Connection":"keep-alive", "content-id" : "<content-id>", "content-hash" : "<content-hash>"}',
        # monitoring page:
        # https://webhook.site/#!/d0dbb19d-2a6f-40be-ad4d-fa9c8b34c8df
    )

    match_message = MatchMessage(
        content_id,
        content_hash,
        [banked_signal],
    )

    action_performer.perform_action(match_message)
