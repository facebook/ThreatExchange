# Copyright (c) Meta Platforms, Inc. and affiliates.

import unittest
from hmalib.common.classification_models import (
    BankedContentIDClassificationLabel,
    BankIDClassificationLabel,
    ClassificationLabel,
)
from hmalib.common.configs.evaluator import ActionLabel, ActionRule
from hmalib.common.messages.match import BankedSignal
from hmalib.common.messages.action import ActionMessage


class ActionMessageTestCase(unittest.TestCase):
    def test_action_message_serialization_and_deserialization(self):
        enqueue_mini_castle_for_review_action_label = ActionLabel(
            "EnqueueMiniCastleForReview"
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
        ]

        banked_signal = BankedSignal(
            banked_content_id="4169895076385542",
            bank_id="303636684709969",
            bank_source="te",
        )
        banked_signal.add_classification("true_positive")

        action_message = ActionMessage(
            content_key="images/mini-castle.jpg",
            content_hash="361da9e6cf1b72f5cea0344e5bb6e70939f4c70328ace762529cac704297354a",
            matching_banked_signals=[banked_signal],
            action_label=enqueue_mini_castle_for_review_action_label,
            action_rules=action_rules,
        )

        action_message_aws_json = action_message.to_aws_json()

        action_message_2 = ActionMessage.from_aws_json(action_message_aws_json)

        self.assertEqual(
            action_message_2.action_label, enqueue_mini_castle_for_review_action_label
        )
