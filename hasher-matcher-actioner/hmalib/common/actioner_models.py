# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import hmalib.common.config as config
import json
import typing as t

from dataclasses import dataclass, field, fields
from hmalib.common.logging import get_logger
from hmalib.common.message_models import MatchMessage
from hmalib.common.classification_models import ActionLabel, Label
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


@dataclass
class WebhookActionPerformer(ActionPerformer):
    """Superclass for webhooks"""

    url: str
    headers: str

    def perform_action(self, match_message: MatchMessage) -> None:
        self.call(data=json.dumps(match_message.to_aws()))

    def call(self, data: str) -> Response:
        raise NotImplementedError()


@dataclass
class WebhookPostActionPerformer(WebhookActionPerformer):
    """Hit an arbitrary endpoint with a POST"""

    def call(self, data: str) -> Response:
        return post(self.url, data, headers=json.loads(self.headers))


@dataclass
class WebhookGetActionPerformer(WebhookActionPerformer):
    """Hit an arbitrary endpoint with a GET"""

    def call(self, data: str) -> Response:
        return get(self.url, headers=json.loads(self.headers))


@dataclass
class WebhookPutActionPerformer(WebhookActionPerformer):
    """Hit an arbitrary endpoint with a PUT"""

    def call(self, data: str) -> Response:
        return put(self.url, data, headers=json.loads(self.headers))


@dataclass
class WebhookDeleteActionPerformer(WebhookActionPerformer):
    """Hit an arbitrary endpoint with a DELETE"""

    def call(self, data: str) -> Response:
        return delete(self.url, headers=json.loads(self.headers))
