# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import typing as t
import unittest

from hmalib.lambdas.actions.action_evaluator import get_action_labels
from hmalib.models import MatchMessage, BankedSignal
from hmalib.common.actioner_models import (
    ActionLabel,
    ActionRule,
    BankedContentIDClassificationLabel,
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
                enqueue_for_review_action_label.value,
                enqueue_for_review_action_label,
                set([BankIDClassificationLabel(bank_id)]),
                set([ClassificationLabel("Foo")]),
            )
        ]

        action_labels: t.Set[ActionLabel] = get_action_labels(
            match_message_without_foo, action_rules
        )

        assert len(action_labels) == 1
        assert action_labels.pop() == enqueue_for_review_action_label

        action_labels = get_action_labels(match_message_with_foo, action_rules)

        assert len(action_labels) == 0

        enqueue_mini_castle_for_review_action_label = ActionLabel(
            "EnqueueMiniCastleForReview"
        )
        enqueue_sailboat_for_review_action_label = ActionLabel(
            "EnqueueSailboatForReview"
        )

        action_rules = [
            ActionRule(
                name="Enqueue Mini-Castle for Review",
                action_label=enqueue_mini_castle_for_review_action_label,
                must_have_labels=set(
                    [
                        BankIDClassificationLabel("303636684709969"),
                        ClassificationLabel("true_positive"),
                    ]
                ),
                must_not_have_labels=set(
                    [BankedContentIDClassificationLabel("3364504410306721")]
                ),
            ),
            ActionRule(
                name="Enqueue Sailboat for Review",
                action_label=enqueue_sailboat_for_review_action_label,
                must_have_labels=set(
                    [
                        BankIDClassificationLabel("303636684709969"),
                        ClassificationLabel("true_positive"),
                        BankedContentIDClassificationLabel("3364504410306721"),
                    ]
                ),
                must_not_have_labels=set(),
            ),
        ]

        mini_castle_match_message = MatchMessage(
            content_key="images/mini-castle.jpg",
            content_hash="361da9e6cf1b72f5cea0344e5bb6e70939f4c70328ace762529cac704297354a",
            matching_banked_signals=[
                BankedSignal(
                    banked_content_id="4169895076385542",
                    bank_id="303636684709969",
                    bank_source="te",
                    classifications=["true_positive"],
                )
            ],
        )

        sailboat_match_message = MatchMessage(
            content_key="images/sailboat-mast-and-sun.jpg",
            content_hash="388ff5e1084efef10096df9cb969296dff2b04d67a94065ecd292129ef6b1090",
            matching_banked_signals=[
                BankedSignal(
                    banked_content_id="3364504410306721",
                    bank_id="303636684709969",
                    bank_source="te",
                    classifications=["true_positive"],
                )
            ],
        )

        action_labels = get_action_labels(mini_castle_match_message, action_rules)

        assert len(action_labels) == 1
        assert action_labels.pop() == enqueue_mini_castle_for_review_action_label

        action_labels = get_action_labels(sailboat_match_message, action_rules)

        assert len(action_labels) == 1
        assert action_labels.pop() == enqueue_sailboat_for_review_action_label
