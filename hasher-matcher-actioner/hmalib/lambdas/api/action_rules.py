# Copyright (c) Meta Platforms, Inc. and affiliates.

import bottle
import typing as t
import sys

from botocore.exceptions import ClientError
from bottle import response
from dataclasses import dataclass, field
from hmalib.common.logging import get_logger
from hmalib.lambdas.api.middleware import (
    jsoninator,
    JSONifiable,
    DictParseable,
    SubApp,
)
from hmalib.common.config import HMAConfig
from hmalib.common import config as hmaconfig
from hmalib.common.configs.evaluator import ActionRule


logger = get_logger(__name__)


@dataclass
class ActionRulesRequest(DictParseable):
    action_rule: ActionRule

    @classmethod
    def from_dict(cls, d: dict) -> "ActionRulesRequest":
        ar = ActionRule.from_aws(d["action_rule"])
        logger.debug("Deserialized ActionRule: %s", ar)
        return cls(ar)


@dataclass
class ActionRulesResponse(JSONifiable):
    error_message: str
    action_rules: t.List[ActionRule] = field(default_factory=list)

    def to_json(self) -> t.Dict:
        return {
            "error_message": self.error_message,
            "action_rules": [action_rule.to_aws() for action_rule in self.action_rules],
        }


# TODO elevate this to some central place when working on Issue 599
def handle_unexpected_error(e: Exception):
    logger.error("Unexpected error: %s", sys.exc_info()[0])
    logger.exception(e)
    response.status = 500


def get_action_rules_api(hma_config_table: str) -> bottle.Bottle:
    # The endpoints below imply a prefix of '/action-rules'
    action_rules_api = SubApp()
    HMAConfig.initialize(hma_config_table)

    @action_rules_api.get("/", apply=[jsoninator])
    def get_action_rules() -> ActionRulesResponse:
        """
        Return all action rules.
        """
        error_message = ""
        action_rules = []

        try:
            action_rules = ActionRule.get_all()
            logger.info("action_rules: %s", action_rules)
        except Exception as e:
            error_message = "Unexpected error."
            handle_unexpected_error(e)

        return ActionRulesResponse(error_message, action_rules)

    @action_rules_api.post("/", apply=[jsoninator(ActionRulesRequest)])
    def create_action_rule(
        request: ActionRulesRequest,
    ) -> ActionRulesResponse:
        """
        Create an action rule.
        """
        logger.info("request: %s", request)
        error_message = ""

        try:
            hmaconfig.create_config(request.action_rule)
        except ClientError as e:
            # TODO this test for "already exists" should be moved to a common place
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                error_message = f"An action rule with the name '{request.action_rule.name}' already exists."
                logger.warning(
                    "Duplicate action rule creation attempted: %s",
                    e.response["Error"]["Message"],
                )
            else:
                error_message = "Unexpected error."
                logger.error(
                    "Unexpected client error: %s", e.response["Error"]["Message"]
                )
                logger.exception(e)
            response.status = 500
        except Exception as e:
            error_message = "Unexpected error."
            handle_unexpected_error(e)

        return ActionRulesResponse(error_message)

    @action_rules_api.put("/<old_name>", apply=[jsoninator(ActionRulesRequest)])
    def update_action_rule(
        request: ActionRulesRequest,
        old_name: str,
    ) -> ActionRulesResponse:
        """
        Update the action rule with name=<oldname>.
        """
        logger.info("old_name: %s", old_name)
        logger.info("request: %s", request)
        error_message = ""

        if ActionRule.exists(request.action_rule.name):
            try:
                hmaconfig.update_config(request.action_rule)
            except Exception as e:
                error_message = "Unexpected error."
                handle_unexpected_error(e)
        elif ActionRule.exists(old_name):
            try:
                hmaconfig.create_config(request.action_rule)
                hmaconfig.delete_config_by_type_and_name("ActionRule", old_name)
            except Exception as e:
                error_message = "Unexpected error."
                handle_unexpected_error(e)
        else:
            error_message = f"An action rule named '{request.action_rule.name}' or '{old_name}' does not exist."
            logger.warning(
                "An attempt was made to update an action rule named either '%s' or '%s' but neither exist.",
                request.action_rule.name,
                old_name,
            )
            response.status = 500

        return ActionRulesResponse(error_message)

    @action_rules_api.delete("/<name>", apply=[jsoninator])
    def delete_action_rule(name: str) -> ActionRulesResponse:
        """
        Delete the action rule with name=<name>.
        """
        logger.info("name: %s", name)
        error_message = ""

        if ActionRule.exists(name):
            try:
                hmaconfig.delete_config_by_type_and_name("ActionRule", name)
            except Exception as e:
                error_message = "Unexpected error."
                handle_unexpected_error(e)
        else:
            error_message = f"An action rule named '{name}' does not exist."
            logger.warning(
                "An attempt was made to delete an action rule named '%s' that does not exist.",
                name,
            )
            response.status = 500

        return ActionRulesResponse(error_message)

    return action_rules_api
