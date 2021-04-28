# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import unittest
import os
import typing as t
from hmalib.lambdas.actions.reactioner import lambda_handler
from hmalib.common.actioner_models import (
    MatchMessage,
    ReactionMessage,
    BankedSignal,
    SawThisTooReactionLabel,
    IngestedReactionLabel,
    InReviewReactionLabel,
    FalsePositiveReactionLabel,
    TruePositiveReactionLabel,
)

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
        event = {"Records": [{"body": reaction_message.to_aws_message()}]}

        result = lambda_handler(event, None)
        assert result == {
            "reactions_performed": {
                "te": "reacted SAW_THIS_TOO to descriptors [12345,67890]"
            }
        }

        os.environ["MOCK_TE_API"] = "False"

    def test_ingested(self):
        os.environ["MOCK_TE_API"] = "True"

        reaction = IngestedReactionLabel()
        reaction_message = ReactionMessage.from_match_message_and_label(
            self.match_message, reaction
        )
        event = {"Records": [{"body": reaction_message.to_aws_message()}]}

        result = lambda_handler(event, None)
        assert result == {
            "reactions_performed": {
                "te": "reacted INGESTED to descriptors [12345,67890]"
            }
        }

        os.environ["MOCK_TE_API"] = "False"

    def test_in_review(self):
        os.environ["MOCK_TE_API"] = "True"

        reaction = InReviewReactionLabel()
        reaction_message = ReactionMessage.from_match_message_and_label(
            self.match_message, reaction
        )
        event = {"Records": [{"body": reaction_message.to_aws_message()}]}

        result = lambda_handler(event, None)
        assert result == {
            "reactions_performed": {
                "te": "reacted IN_REVIEW to descriptors [12345,67890]"
            }
        }

        os.environ["MOCK_TE_API"] = "False"

    def test_false_positve(self):
        os.environ["MOCK_TE_API"] = "True"

        reaction = FalsePositiveReactionLabel()
        reaction_message = ReactionMessage.from_match_message_and_label(
            self.match_message, reaction
        )
        event = {"Records": [{"body": reaction_message.to_aws_message()}]}

        result = lambda_handler(event, None)
        assert result == {"reactions_performed": {"te": "Wrote Back false positive"}}

        os.environ["MOCK_TE_API"] = "False"

    def test_true_positve(self):
        os.environ["MOCK_TE_API"] = "True"

        reaction = TruePositiveReactionLabel()
        reaction_message = ReactionMessage.from_match_message_and_label(
            self.match_message, reaction
        )
        event = {"Records": [{"body": reaction_message.to_aws_message()}]}

        result = lambda_handler(event, None)
        assert result == {"reactions_performed": {"te": "Wrote Back true positive"}}

        os.environ["MOCK_TE_API"] = "False"

    # def test_second_writebacker(self):
    #     class NonTEWritebacker(Writebacker):
    #         """
    #         Writebacker parent object for all writebacks to ThreatExchange
    #         """

    #         source = "non-te-source"

    #         @staticmethod
    #         def writeback_options() -> t.List[t.Type["NonTEWritebacker"]]:
    #             return [NonTEFalsePositveWritebacker]

    #         def writeback_is_enabled(self) -> bool:
    #             return True

    #     class NonTEFalsePositveWritebacker(NonTEWritebacker):
    #         reaction_label = FalsePositiveReactionLabel()

    #         def _writeback_impl(self, writeback_message: ReactionMessage) -> str:
    #             return "Wrote Back false positive to non TE source"

    #     os.environ["MOCK_TE_API"] = "True"

    #     reaction = FalsePositiveReactionLabel()
    #     reaction_message = ReactionMessage.from_match_message_and_label(
    #         self.match_message, reaction
    #     )
    #     event = {"Records": [{"body": reaction_message.to_aws_message()}]}

    #     result = lambda_handler(event, None)
    #     assert result == {
    #         "reactions_performed": {
    #             "te": "Wrote Back false positive",
    #             "non-te-source": "Wrote Back false positive to non TE source",
    #         }
    #     }

    #     os.environ["MOCK_TE_API"] = "False"
