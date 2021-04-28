# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import unittest
import os
import typing as t
from hmalib.lambdas.actions.reactioner import lambda_handler
from hmalib.common.label_models import (
    SawThisTooReactionLabel,
    IngestedReactionLabel,
    FalsePositiveReactionLabel,
    TruePositiveReactionLabel,
)
from hmalib.common.message_models import MatchMessage, ReactionMessage, BankedSignal

from hmalib.common.reactioner_models import Writebacker


class WritebackerTestCase(unittest.TestCase):

    banked_signals = [
        BankedSignal("2862392437204724", "bank 4", "te"),
        BankedSignal("4194946153908639", "bank 4", "te"),
        BankedSignal("4194946153908639", "bank 4", "non-te-source"),
    ]

    match_message = MatchMessage("key", "hash", banked_signals)

    def test_saw_this_too(self):
        os.environ["MOCK_TE_API"] = "True"

        reaction = SawThisTooReactionLabel()
        reaction_message = ReactionMessage.from_match_message_and_label(
            self.match_message, reaction
        )
        event = {"Records": [{"body": reaction_message.to_aws_json()}]}

        result = lambda_handler(event, None)
        assert result == {
            "reactions_performed": {"te": "reacted SAW_THIS_TOO to 2 descriptors"}
        }

        os.environ["MOCK_TE_API"] = "False"

    def test_ingested(self):
        os.environ["MOCK_TE_API"] = "True"

        reaction = IngestedReactionLabel()
        reaction_message = ReactionMessage.from_match_message_and_label(
            self.match_message, reaction
        )
        event = {"Records": [{"body": reaction_message.to_aws_json()}]}

        result = lambda_handler(event, None)
        assert result == {
            "reactions_performed": {"te": "reacted INGESTED to 2 descriptors"}
        }

        os.environ["MOCK_TE_API"] = "False"

    def test_false_positve(self):
        os.environ["MOCK_TE_API"] = "True"

        reaction = FalsePositiveReactionLabel()
        reaction_message = ReactionMessage.from_match_message_and_label(
            self.match_message, reaction
        )
        event = {"Records": [{"body": reaction_message.to_aws_json()}]}

        result = lambda_handler(event, None)
        assert result == {"reactions_performed": {"te": "Wrote Back false positive"}}

        os.environ["MOCK_TE_API"] = "False"

    def test_true_positve(self):
        os.environ["MOCK_TE_API"] = "True"

        reaction = TruePositiveReactionLabel()
        reaction_message = ReactionMessage.from_match_message_and_label(
            self.match_message, reaction
        )
        event = {"Records": [{"body": reaction_message.to_aws_json()}]}

        result = lambda_handler(event, None)
        assert result == {"reactions_performed": {"te": "Wrote Back true positive"}}

        os.environ["MOCK_TE_API"] = "False"
