# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import unittest
import os
from hmalib.common.actioner_models import (
    ActionLabel,
    ActionPerformerConfig,
    BankedSignal,
    MatchMessage,
)

from hmalib.common.reactioner_models import (
    ReactInReviewActionPerformer,
    ReactSawThisTooActionPerformer,
)


class TestActioner(unittest.TestCase):
    @staticmethod
    def mock_aws_credentials():
        """
        Mocked AWS Credentials for moto.
        (likely not needed based on local testing but just incase)
        """
        os.environ["AWS_ACCESS_KEY_ID"] = "testing"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
        os.environ["AWS_SECURITY_TOKEN"] = "testing"
        os.environ["AWS_SESSION_TOKEN"] = "testing"

    @classmethod
    def setUpClass(cls):
        cls.mock_aws_credentials()

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
