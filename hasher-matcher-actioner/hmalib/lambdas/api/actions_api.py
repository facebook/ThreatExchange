# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import bottle
import typing as t
from dataclasses import dataclass, asdict
from .middleware import jsoninator, JSONifiable, DictParseable
from hmalib.common.config import HMAConfig, update_config
from hmalib.common import config as hmaconfig
from hmalib.common.actioner_models import ActionPerformer


@dataclass
class Action(JSONifiable, DictParseable):
    name: str
    config_subtype: str
    url: str
    headers: str

    def to_json(self) -> t.Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Action":
        return cls(
            d["name"],
            d["config_subtype"],
            d["url"] if d["url"] else "",
            d["headers"] if d["headers"] else "",
        )


@dataclass
class ActionsResponse(JSONifiable):
    actions_response: t.List[Action]

    def to_json(self) -> t.Dict:
        return {
            "actions_response": [action.to_json() for action in self.actions_response]
        }


@dataclass
class DeleteActionResponse(JSONifiable):
    response: str

    def to_json(self) -> t.Dict:
        return asdict(self)


@dataclass
class CreateActionResponse(JSONifiable):
    response: str

    def to_json(self) -> t.Dict:
        return asdict(self)


def get_actions_api(hma_config_table: str) -> bottle.Bottle:
    # The documentation below expects prefix to be '/actions/'
    actions_api = bottle.Bottle()
    HMAConfig.initialize(hma_config_table)

    @actions_api.get("/", apply=[jsoninator])
    def get_actions() -> ActionsResponse:
        """
        Returns all action configs.
        """
        action_configs = ActionPerformer.get_all()
        return ActionsResponse(
            actions_response=[
                Action.from_dict(config.__dict__) for config in action_configs
            ]
        )

    @actions_api.post("/update", apply=[jsoninator(Action)])
    def update_action(request: Action) -> t.Optional[Action]:
        """
        Update an action url and headers
        """
        sub_types = ActionPerformer.get_subtype_classes()
        for sub_type in sub_types:
            if sub_type.get_config_subtype() == request.config_subtype:
                config = sub_type.getx(request.name)
                config.url = request.url
                config.headers = request.headers
                updated_config = hmaconfig.update_config(config)
                return Action.from_dict(updated_config.__dict__)

        raise ValueError("The request is invalid!")

    @actions_api.post("/create", apply=[jsoninator(Action)])
    def create_action(request: Action) -> CreateActionResponse:
        """
        create an action
        """
        sub_types = ActionPerformer.get_subtype_classes()
        for sub_type in sub_types:
            if sub_type.get_config_subtype() == request.config_subtype:
                config = sub_type(
                    name=request.name, url=request.url, headers=request.headers
                )
                hmaconfig.create_config(config)
                return CreateActionResponse(response="The action config is created.")
        raise ValueError("The request is invalid!")

    @actions_api.post("/delete/<key>", apply=[jsoninator])
    def delete_action(key=None) -> DeleteActionResponse:
        """
        Delete an action
        """
        config = ActionPerformer.getx(str(key))
        hmaconfig.delete_config(config)
        return DeleteActionResponse(response="The action config is deleted.")

    return actions_api
