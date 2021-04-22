# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import typing as t
import unittest

from hmalib.lambdas.actions.action_evaluator import get_action_labels
from hmalib.models import MatchMessage, BankedSignal
from hmalib.common.actioner_models import (
    ActionLabel,
    ActionRule,
    BankIDClassificationLabel,
    ClassificationLabel,
    Label,
)


class ActionRuleEvaluationTestCase(unittest.TestCase):
    def test_get_action_labels(self):

        enqueue_for_review_action_label = ActionLabel("EnqueueForReview")
        bank_id = "12345"

        banked_signal_without_foo = BankedSignal(
            "67890", bank_id, "Test", ["Bar", "Xyz"]
        )
        banked_signal_with_foo = BankedSignal(
            "67890", bank_id, "Test", ["Foo", "Bar", "Xyz"]
        )

        match_message_without_foo = MatchMessage(
            "key", "hash", [banked_signal_without_foo]
        )
        match_message_with_foo = MatchMessage("key", "hash", [banked_signal_with_foo])

        action_rules = [
            ActionRule(
                enqueue_for_review_action_label,
                [BankIDClassificationLabel(bank_id)],
                [ClassificationLabel("Foo")],
            )
        ]

        action_labels: t.Set[ActionLabel] = get_action_labels(
            match_message_without_foo, action_rules
        )

        assert len(action_labels) == 1
        assert action_labels.pop() == enqueue_for_review_action_label

        action_labels = get_action_labels(match_message_with_foo, action_rules)

        assert len(action_labels) == 0
