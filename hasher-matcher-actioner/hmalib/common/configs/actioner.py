# Copyright (c) Meta Platforms, Inc. and affiliates.

import hmalib.common.config as config
import json
import typing as t

from dataclasses import dataclass, field
from hmalib.common.logging import get_logger
from hmalib.common.extension import load_actioner_performer_extension
from hmalib.common.messages.action import ActionMessage
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

    ActionPerformer.get("action_name").perform_action(message)
    """

    @staticmethod
    def get_subtype_classes():
        return [
            WebhookPostActionPerformer,
            WebhookGetActionPerformer,
            WebhookPutActionPerformer,
            WebhookDeleteActionPerformer,
            CustomImplActionPerformer,
        ]

    # Implemented by subtypes
    def perform_action(self, message: ActionMessage) -> None:
        raise NotImplementedError


# at match time, these strings are replaced by the result of running the associated
# function on the match message
WEBHOOK_ACTION_PERFORMER_REPLACEMENTS: t.Dict[str, t.Callable[[ActionMessage], str]] = {
    "<content-id>": lambda message: message.content_key,
}


@dataclass
class WebhookActionPerformer(ActionPerformer):
    """Superclass for webhooks"""

    url: str
    headers: str

    def perform_action(self, message: ActionMessage) -> None:
        parsed_url = self.url
        for (
            replacement_str,
            replacement_func,
        ) in WEBHOOK_ACTION_PERFORMER_REPLACEMENTS.items():
            parsed_url = parsed_url.replace(replacement_str, replacement_func(message))
        self.call(parsed_url, data=json.dumps(message.to_aws()))

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


@dataclass
class CustomImplActionPerformer(ActionPerformer):
    """
    Pulls values from extensions.py for an action performer impl.
    Requires configuration in setting.py and hma_extensions as well.
    """

    extension_name: str
    additional_kwargs: t.Dict[str, str] = field(default_factory=dict)

    def perform_action(self, message: ActionMessage) -> None:
        if ext := load_actioner_performer_extension(self.extension_name):
            ext.perform_action_impl(message, self.additional_kwargs)
        else:
            logger.error(
                f"Unable to load custom action performer: {self.extension_name}"
            )
