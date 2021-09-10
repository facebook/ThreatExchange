# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import hmalib.common.config as config
import json
import typing as t

from dataclasses import dataclass
from hmalib.common.logging import get_logger
from hmalib.common.messages.match import MatchMessage
from hmalib.common.aws_dataclass import HasAWSSerialization
from requests import get, post, put, delete, Response

logger = get_logger(__name__)


TUrl = t.Union[t.Text, bytes]

# This class should be kept in sync with typescript class BackendActionPerformer in API.tsx
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
}


@dataclass
class WebhookActionPerformer(ActionPerformer):
    """Superclass for webhooks"""

    url: str
    headers: str

    def perform_action(self, match_message: MatchMessage) -> None:
        parsed_url = self.url
        for (
            replacement_str,
            replacement_func,
        ) in WEBHOOK_ACTION_PERFORMER_REPLACEMENTS.items():
            parsed_url = parsed_url.replace(
                replacement_str, replacement_func(match_message)
            )
        self.call(parsed_url, data=json.dumps(match_message.to_aws()))

    def call(self, url: str, data: str) -> Response:
        raise NotImplementedError()


@dataclass
class WebhookPostActionPerformer(WebhookActionPerformer):
    """Hit an arbitrary endpoint with a POST"""

    def call(self, url: str, data: str) -> Response:
        logger.info(f"Performing a POST request to URL. {url}")
        return post(url, data, headers=json.loads(self.headers))


@dataclass
class WebhookGetActionPerformer(WebhookActionPerformer):
    """Hit an arbitrary endpoint with a GET"""

    def call(self, url: str, data: str) -> Response:
        logger.info(f"Performing a GET request to URL. {url}")
        return get(url, headers=json.loads(self.headers))


@dataclass
class WebhookPutActionPerformer(WebhookActionPerformer):
    """Hit an arbitrary endpoint with a PUT"""

    def call(self, url: str, data: str) -> Response:
        logger.info(f"Performing a PUT request to URL. {url}")
        return put(url, data, headers=json.loads(self.headers))


@dataclass
class WebhookDeleteActionPerformer(WebhookActionPerformer):
    """Hit an arbitrary endpoint with a DELETE"""

    def call(self, url: str, data: str) -> Response:
        logger.info(f"Performing a DELETE request to URL. {url}")
        return delete(url, headers=json.loads(self.headers))
