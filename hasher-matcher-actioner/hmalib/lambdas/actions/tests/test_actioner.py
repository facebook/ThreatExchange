# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import unittest
from hmalib.common.actioner_models import (
    ActionLabel,
    ActionPerformerConfig,
    BankedSignal,
    MatchMessage
)

from hmalib.common.reactioner_models import (
    ReactInReviewActionPerformer,
    ReactSawThisTooActionPerformer,
)

class TestActioner(unittest.TestCase):
    def test_react_action(self):
        banked_signals = [
            BankedSignal("2862392437204724", "bank 4", "te"),
            BankedSignal("4194946153908639", "bank 4", "te"),
        ]
        match_message = MatchMessage("key", "hash", banked_signals)

        configs: t.List[ActionPerformer] = [
            ReactInReviewActionPerformer(
                action_label=ActionLabel("ReactInReview"),
            ),
            ReactSawThisTooActionPerformer(
                action_label=ActionLabel("ReactSawThisToo"),
            ),
        ]
        for config in configs:
            config.perform_action(match_message)

    def test_react_non_te(self):
        banked_signals = [
            BankedSignal("2862392437204724", "bank 4", "te"),
            BankedSignal("4194946153908639", "bank 4", "te"),
        ]
        match_message = MatchMessage("key", "hash", banked_signals)

        configs: t.List[ActionPerformer] = [
            ReactInReviewActionPerformer(
                action_label=ActionLabel("ReactInReview"),
            ),
            ReactSawThisTooActionPerformer(
                action_label=ActionLabel("ReactSawThisToo"),
            ),
        ]
        for config in configs:
            config.perform_action(match_message)
