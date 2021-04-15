# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

from dataclasses import dataclass
import typing as t

from hmalib.models import Label, MatchMessage

from requests import get, post, put, delete, Response


class LabelWithConstraints(Label):
    _KEY_CONSTRAINT = "KeyConstraint"

    def __init__(self, value: str):
        super(LabelWithConstraints, self).__init__(self._KEY_CONSTRAINT, value)


class ActionLabel(LabelWithConstraints):
    _KEY_CONSTRAINT = "Action"

    def __hash__(self) -> int:
        return self.value.__hash__()


class ThreatExchangeReactionLabel(LabelWithConstraints):
    _KEY_CONSTRAINT = "ThreatExchangeReaction"


@dataclass
class Action:
    action_label: ActionLabel
    priority: int
    superseded_by: t.List[ActionLabel]


@dataclass
class ActionRule:
    action_label: ActionLabel
    must_have_labels: t.List[Label]
    must_not_have_labels: t.List[Label]


TUrl = t.Union[t.Text, bytes]


class HTTPRequest:
    @staticmethod
    def call(url: TUrl, **kwargs) -> Response:
        raise NotImplementedError()


class Post(HTTPRequest):
    @staticmethod
    def call(url: TUrl, **kwargs) -> Response:
        data = kwargs.get("data")
        return post(url, data)


class Get(HTTPRequest):
    @staticmethod
    def call(url: TUrl, **kwargs) -> Response:
        return get(url)


class Put(HTTPRequest):
    @staticmethod
    def call(url: TUrl, **kwargs) -> Response:
        data = kwargs.get("data")
        return put(url, data)


class Delete(HTTPRequest):
    @staticmethod
    def call(url: TUrl, **kwargs) -> Response:
        return delete(url)


class ActionPerformer:
    def perform_action(self, match_message: MatchMessage) -> None:
        raise NotImplementedError()


@dataclass
class WebhookActionPerformer(ActionPerformer):

    request_type: t.Type[HTTPRequest]
    url: TUrl

    def perform_action(self, match_message: MatchMessage) -> None:
        kwargs = {"url": self.url, "data": match_message.to_sns_message()}
        self.request_type.call(**kwargs)
