# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import unittest

import os
import typing as t
from hmalib.lambdas.actions.writebacker import lambda_handler
from hmalib.common.classification_models import WritebackTypes
from hmalib.common.message_models import MatchMessage, WritebackMessage, BankedSignal

from hmalib.common.fetcher_models import ThreatExchangeConfig

from hmalib.common import config as hmaconfig

from hmalib.common.writebacker_models import Writebacker


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
        ThreatExchangeConfig("pg 4", True, "Trustworthy PG", True, True),
        ThreatExchangeConfig("pg 3", True, "UnTrustworthy PG", True, False),
    ]

    for config in configs:
        hmaconfig.mock_create_config(config)

    def test_saw_this_too(self):
        os.environ["MOCK_TE_API"] = "True"

        writeback = WritebackTypes.SawThisToo
        writeback_message = WritebackMessage.from_match_message_and_label(
            self.match_message, writeback
        )
        event = {"Records": [{"body": writeback_message.to_aws_json()}]}

        result = lambda_handler(event, None)
        assert result == {
            "writebacks_performed": {
                "te": [
                    "reacted SAW_THIS_TOO to 1 descriptors",
                    "reacted SAW_THIS_TOO to 1 descriptors",
                    "No writeback performed for banked content id 3027465034605137 becuase writebacks were disabled",
                ]
            }
        }

        os.environ["MOCK_TE_API"] = "False"

    def test_ingested(self):
        os.environ["MOCK_TE_API"] = "True"

        writeback = WritebackTypes.Ingested
        writeback_message = WritebackMessage.from_match_message_and_label(
            self.match_message, writeback
        )
        event = {"Records": [{"body": writeback_message.to_aws_json()}]}

        result = lambda_handler(event, None)
        assert result == {
            "writebacks_performed": {
                "te": [
                    "reacted INGESTED to 1 descriptors",
                    "reacted INGESTED to 1 descriptors",
                    "No writeback performed for banked content id 3027465034605137 becuase writebacks were disabled",
                ]
            }
        }

        os.environ["MOCK_TE_API"] = "False"

    def test_false_positve(self):
        os.environ["MOCK_TE_API"] = "True"

        writeback = WritebackTypes.FalsePositive
        writeback_message = WritebackMessage.from_match_message_and_label(
            self.match_message, writeback
        )
        event = {"Records": [{"body": writeback_message.to_aws_json()}]}

        result = lambda_handler(event, None)
        assert result == {
            "writebacks_performed": {
                "te": [
                    "Wrote back false positive on indicator 2862392437204724",
                    "Wrote back false positive on indicator 4194946153908639",
                    "No writeback performed for banked content id 3027465034605137 becuase writebacks were disabled",
                ]
            }
        }

        os.environ["MOCK_TE_API"] = "False"

    def test_true_positve(self):
        os.environ["MOCK_TE_API"] = "True"

        writeback = WritebackTypes.TruePositive
        writeback_message = WritebackMessage.from_match_message_and_label(
            self.match_message, writeback
        )
        event = {"Records": [{"body": writeback_message.to_aws_json()}]}

        result = lambda_handler(event, None)
        assert result == {
            "writebacks_performed": {
                "te": [
                    "Wrote back true positive on indicator 2862392437204724",
                    "Wrote back true positive on indicator 4194946153908639",
                    "No writeback performed for banked content id 3027465034605137 becuase writebacks were disabled",
                ]
            }
        }

        os.environ["MOCK_TE_API"] = "False"
