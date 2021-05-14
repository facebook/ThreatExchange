# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import bottle
import typing as t
from dataclasses import dataclass
from hmalib.common.logging import get_logger
from .middleware import jsoninator, JSONifiable
from hmalib.common.config import HMAConfig
from hmalib.common.evaluator_models import ActionRule

logger = get_logger(__name__)


@dataclass
class ActionRulesResponse(JSONifiable):
    action_rules: t.List[ActionRule]

    def to_json(self) -> t.Dict:
        return {
            "action_rules": [action_rule.to_aws() for action_rule in self.action_rules]
        }


def get_action_rules_api(hma_config_table: str) -> bottle.Bottle:
    # The documentation below expects prefix to be '/action-rules/'
    action_rules_api = bottle.Bottle()
    HMAConfig.initialize(hma_config_table)

    @action_rules_api.get("/", apply=[jsoninator])
    def action_rules() -> ActionRulesResponse:
        """
        Returns all action rules.
        """
        action_rules = ActionRule.get_all()
        logger.info("action_rules: %s", action_rules)
        return ActionRulesResponse(action_rules=action_rules)

    return action_rules_api
