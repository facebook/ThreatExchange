# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import unittest
import os
from hmalib.lambdas.actions.reactioner import lambda_handler
from hmalib.common.actioner_models import (
    MatchMessage,
    ReactionMessage,
    BankedSignal,
    ThreatExchangeReactionLabel,
)


class WritebackerTestCase(unittest.TestCase):
    def test_writeback_suceededs(self):
        os.environ["MOCK_TE_API"] = "True"

        writebacks = [
            "ThreatExchangeFalsePositiveWritebacker",
            "ThreatExchangeTruePositivePositiveWritebacker",
            "ThreatExchangeInReviewWritebacker",
            "ThreatExchangeIngestedWritebacker",
            "ThreatExchangeSawThisTooWritebacker",
        ]

        for writeback in writebacks:
            banked_signals = [
                BankedSignal("2862392437204724", "bank 4", "te"),
                BankedSignal("4194946153908639", "bank 4", "te"),
            ]

            match_message = MatchMessage("key", "hash", banked_signals)

            reaction = ThreatExchangeReactionLabel(writeback)

            reaction_message = ReactionMessage.from_match_message_and_label(
                match_message, reaction
            )

            event = {"Records": [{"body": reaction_message.to_aws_message()}]}

            result = lambda_handler(event, None)
            assert result == {"reaction_performed": writeback}

        os.environ["MOCK_TE_API"] = "False"
