# Copyright (c) Meta Platforms, Inc. and affiliates.

import bottle
import typing as t
from dataclasses import dataclass, asdict
from hmalib.lambdas.api.middleware import (
    jsoninator,
    JSONifiable,
    DictParseable,
    SubApp,
)
from hmalib.common.config import HMAConfig
from hmalib.common import config as hmaconfig
from hmalib.common.configs.actioner import ActionPerformer


@dataclass
class FetchAllActionsResponse(JSONifiable):
    actions_response: t.List[t.Dict[str, t.Any]]

    def to_json(self) -> t.Dict:
        return {"actions_response": [action for action in self.actions_response]}


@dataclass
class CreateUpdateActionRequest(DictParseable):
    name: str
    config_subtype: str
    fields: t.Dict[str, t.Any]

    @classmethod
    def from_dict(cls, d: dict) -> "CreateUpdateActionRequest":
        return cls(
            d["name"],
            d["config_subtype"],
            d["fields"],
        )


@dataclass
class CreateActionResponse(JSONifiable):
    response: str

    def to_json(self) -> t.Dict:
        return asdict(self)


@dataclass
class UpdateActionResponse(JSONifiable):
    response: str

    def to_json(self) -> t.Dict:
        return asdict(self)


@dataclass
class DeleteActionResponse(JSONifiable):
    response: str

    def to_json(self) -> t.Dict:
        return asdict(self)


def get_actions_api(hma_config_table: str) -> bottle.Bottle:
    # The documentation below expects prefix to be '/actions/'
    actions_api = SubApp()
    HMAConfig.initialize(hma_config_table)

    @actions_api.get("/", apply=[jsoninator])
    def fetch_all_actions() -> FetchAllActionsResponse:
        """
        Return all action configs.
        """
        action_configs = ActionPerformer.get_all()
        return FetchAllActionsResponse(
            actions_response=[config.__dict__ for config in action_configs]
        )

    @actions_api.put(
        "/<old_name>/<old_config_sub_stype>",
        apply=[jsoninator(CreateUpdateActionRequest)],
    )
    def update_action(
        request: CreateUpdateActionRequest, old_name: str, old_config_sub_stype: str
    ) -> UpdateActionResponse:
        """
        Update the action, name, url, and headers for action with name=<old_name> and subtype=<old_config_sub_stype>.
        """
        if old_name != request.name or old_config_sub_stype != request.config_subtype:
            # The name field can't be updated because it is the primary key
            # The config sub type can't be updated because it is the config class level param
            delete_action(old_name)
            create_action(request)
        else:
            config = ActionPerformer._get_subtypes_by_name()[
                request.config_subtype
            ].getx(request.name)
            for key, value in request.fields.items():
                setattr(config, key, value)
            hmaconfig.update_config(config)
        return UpdateActionResponse(response="The action config is updated.")

    @actions_api.post("/", apply=[jsoninator(CreateUpdateActionRequest)])
    def create_action(request: CreateUpdateActionRequest) -> CreateActionResponse:
        """
        Create an action.
        """
        config = ActionPerformer._get_subtypes_by_name()[request.config_subtype](
            **{"name": request.name, **request.fields}
        )
        hmaconfig.create_config(config)
        return CreateActionResponse(response="The action config is created.")

    @actions_api.delete("/<name>", apply=[jsoninator])
    def delete_action(name: str) -> DeleteActionResponse:
        """
        Delete the action with name=<name>.
        """
        hmaconfig.delete_config_by_type_and_name("ActionPerformer", name)
        return DeleteActionResponse(response="The action config is deleted.")

    return actions_api
