# Copyright (c) Meta Platforms, Inc. and affiliates.

import unittest
import os


from hmalib.lambdas.actions.writebacker import lambda_handler
from hmalib.common.classification_models import WritebackTypes
from hmalib.common.messages.match import MatchMessage, BankedSignal
from hmalib.common.messages.writeback import WritebackMessage
from hmalib.common.configs.fetcher import ThreatExchangeConfig
from hmalib.common import config as hmaconfig


class WritebackerTestCase(unittest.TestCase):

    banked_signals = [
        BankedSignal("2862392437204724", "pg 4", "te"),
        BankedSignal("4194946153908639", "pg 4", "te"),
        BankedSignal("3027465034605137", "pg 3", "te"),
        BankedSignal("evil.jpg", "bank 4", "non-te-source"),
    ]

    match_message = MatchMessage("key", "hash", banked_signals)

    # Writebacks are enabled for the trustworth privacy group not for
    # the untrustworthy one
    configs = [
        ThreatExchangeConfig(
            name="pg 4",
            in_use=True,
            privacy_group_name="Trustworthy PG",
            description="test description",
            fetcher_active=True,
            write_back=True,
            matcher_active=True,
        ),
        ThreatExchangeConfig(
            name="pg 3",
            in_use=True,
            privacy_group_name="UnTrustworthy PG",
            description="test description",
            fetcher_active=True,
            write_back=False,
            matcher_active=True,
        ),
    ]

    for config in configs:
        hmaconfig.mock_create_config(config)

    def test_saw_this_too(self):
        os.environ["MOCK_TE_API"] = "True"
        os.environ["CONFIG_TABLE_NAME"] = "test-HMAConfig"

        writeback = WritebackTypes.SawThisToo
        writeback_message = WritebackMessage.from_match_message_and_type(
            self.match_message, writeback
        )
        event = {"Records": [{"body": writeback_message.to_aws_json()}]}

        result = lambda_handler(event, None)
        assert result == {
            "writebacks_performed": {
                "te": [
                    "Reacted SAW_THIS_TOO to descriptor a2|2862392437204724\nReacted SAW_THIS_TOO to descriptor a3|2862392437204724",
                    "Reacted SAW_THIS_TOO to descriptor a2|4194946153908639\nReacted SAW_THIS_TOO to descriptor a3|4194946153908639",
                    "No writeback performed for banked content id 3027465034605137 becuase writebacks were disabled",
                ]
            }
        }

        os.environ["MOCK_TE_API"] = "False"

    def test_false_positive(self):
        os.environ["MOCK_TE_API"] = "True"
        os.environ["CONFIG_TABLE_NAME"] = "test-HMAConfig"

        writeback = WritebackTypes.FalsePositive
        writeback_message = WritebackMessage.from_match_message_and_type(
            self.match_message, writeback
        )
        event = {"Records": [{"body": writeback_message.to_aws_json()}]}

        result = lambda_handler(event, None)
        assert result == {
            "writebacks_performed": {
                "te": [
                    "Reacted DISAGREE_WITH_TAGS to descriptor a2|2862392437204724\nReacted DISAGREE_WITH_TAGS to descriptor a3|2862392437204724",
                    "Reacted DISAGREE_WITH_TAGS to descriptor a2|4194946153908639\nReacted DISAGREE_WITH_TAGS to descriptor a3|4194946153908639",
                    "No writeback performed for banked content id 3027465034605137 becuase writebacks were disabled",
                ]
            }
        }

        os.environ["MOCK_TE_API"] = "False"

    def test_true_positve(self):
        os.environ["MOCK_TE_API"] = "True"
        os.environ["CONFIG_TABLE_NAME"] = "test-HMAConfig"

        writeback = WritebackTypes.TruePositive
        writeback_message = WritebackMessage.from_match_message_and_type(
            self.match_message, writeback
        )
        event = {"Records": [{"body": writeback_message.to_aws_json()}]}

        result = lambda_handler(event, None)
        assert result == {
            "writebacks_performed": {
                "te": [
                    "Wrote back TruePositive for indicator 2862392437204724\nBuilt descriptor a1|2862392437204724 with privacy groups pg 4",
                    "Wrote back TruePositive for indicator 4194946153908639\nBuilt descriptor a1|4194946153908639 with privacy groups pg 4",
                    "No writeback performed for banked content id 3027465034605137 becuase writebacks were disabled",
                ]
            }
        }

        os.environ["MOCK_TE_API"] = "False"

    def test_remove_opinion(self):
        os.environ["MOCK_TE_API"] = "True"
        os.environ["CONFIG_TABLE_NAME"] = "test-HMAConfig"

        writeback = WritebackTypes.RemoveOpinion
        writeback_message = WritebackMessage.from_match_message_and_type(
            self.match_message, writeback
        )
        event = {"Records": [{"body": writeback_message.to_aws_json()}]}

        result = lambda_handler(event, None)
        assert result == {
            "writebacks_performed": {
                "te": [
                    "\n".join(
                        (
                            "Deleted decriptor a1|2862392437204724 for indicator 2862392437204724",
                            "Removed reaction DISAGREE_WITH_TAGS from descriptor a2|2862392437204724",
                            "Removed reaction DISAGREE_WITH_TAGS from descriptor a3|2862392437204724",
                        )
                    ),
                    "\n".join(
                        (
                            "Deleted decriptor a1|4194946153908639 for indicator 4194946153908639",
                            "Removed reaction DISAGREE_WITH_TAGS from descriptor a2|4194946153908639",
                            "Removed reaction DISAGREE_WITH_TAGS from descriptor a3|4194946153908639",
                        )
                    ),
                    "No writeback performed for banked content id 3027465034605137 becuase writebacks were disabled",
                ]
            }
        }

        os.environ["MOCK_TE_API"] = "False"
