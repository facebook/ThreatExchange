# Copyright (c) Meta Platforms, Inc. and affiliates.

from hmalib.common.configs.actioner import WebhookActionPerformer
import typing as t
import unittest

from hmalib.common.configs.evaluator import (
    ActionLabel,
    ActionRule,
)
from hmalib.common.classification_models import (
    BankedContentIDClassificationLabel,
    BankIDClassificationLabel,
    ClassificationLabel,
)
from hmalib.common.messages.match import BankedSignal, MatchMessage
from hmalib.lambdas.actions.action_evaluator import get_actions_to_take


class ActionRuleEvaluationTestCase(unittest.TestCase):
    def test_get_action_labels(self):

        enqueue_for_review_action_label = ActionLabel("EnqueueForReview")
        bank_id = "12345"

        banked_signal_without_foo = BankedSignal("67890", bank_id, "Test")
        banked_signal_without_foo.add_classification("Bar")
        banked_signal_without_foo.add_classification("Xyz")

        banked_signal_with_foo = BankedSignal("67890", bank_id, "Test")
        banked_signal_with_foo.add_classification("Foo")
        banked_signal_with_foo.add_classification("Bar")
        banked_signal_with_foo.add_classification("Xyz")

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

        action_label_to_action_rules: t.Dict[
            ActionLabel, t.List[ActionRule]
        ] = get_actions_to_take(match_message_without_foo, action_rules, set())

        assert len(action_label_to_action_rules) == 1
        self.assertIn(
            enqueue_for_review_action_label,
            action_label_to_action_rules,
            "enqueue_for_review_action_label should be in action_label_to_action_rules",
        )

        action_label_to_action_rules = get_actions_to_take(
            match_message_with_foo, action_rules, set()
        )

        assert len(action_label_to_action_rules) == 0

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

        mini_castle_banked_signal = BankedSignal(
            banked_content_id="4169895076385542",
            bank_id="303636684709969",
            bank_source="te",
        )
        mini_castle_banked_signal.add_classification("true_positive")

        mini_castle_match_message = MatchMessage(
            content_key="images/mini-castle.jpg",
            content_hash="361da9e6cf1b72f5cea0344e5bb6e70939f4c70328ace762529cac704297354a",
            matching_banked_signals=[mini_castle_banked_signal],
        )

        sailboat_banked_signal = BankedSignal(
            banked_content_id="3364504410306721",
            bank_id="303636684709969",
            bank_source="te",
        )
        sailboat_banked_signal.add_classification("true_positive")

        sailboat_match_message = MatchMessage(
            content_key="images/sailboat-mast-and-sun.jpg",
            content_hash="388ff5e1084efef10096df9cb969296dff2b04d67a94065ecd292129ef6b1090",
            matching_banked_signals=[sailboat_banked_signal],
        )

        action_label_to_action_rules = get_actions_to_take(
            mini_castle_match_message, action_rules, set()
        )

        assert len(action_label_to_action_rules) == 1
        self.assertIn(
            enqueue_mini_castle_for_review_action_label,
            action_label_to_action_rules,
            "enqueue_mini_castle_for_review_action_label should be in action_label_to_action_rules",
        )

        action_label_to_action_rules = get_actions_to_take(
            sailboat_match_message, action_rules, set()
        )

        assert len(action_label_to_action_rules) == 1
        self.assertIn(
            enqueue_sailboat_for_review_action_label,
            action_label_to_action_rules,
            "enqueue_sailboat_for_review_action_label should be in action_label_to_action_rules",
        )

    def test_webhook_action_repalcement(self):
        content_id = "cid1"
        content_hash = "0374f1g34f12g34f8"

        banked_signal = BankedSignal(
            banked_content_id="4169895076385542",
            bank_id="303636684709969",
            bank_source="te",
        )

        match_message = MatchMessage(
            content_id,
            content_hash,
            [banked_signal],
        )

        action_performers = [
            performer_class(
                name="EnqueueForReview",
                url="https://webhook.site/d0dbb19d-2a6f-40be-ad4d-fa9c8b34c8df/<content-id>",
                headers='{"Connection":"keep-alive"}',
                # monitoring page:
                # https://webhook.site/#!/d0dbb19d-2a6f-40be-ad4d-fa9c8b34c8df
            )
            for performer_class in WebhookActionPerformer.__subclasses__()
        ]

        for action_performer in action_performers:
            action_performer.perform_action(match_message)
