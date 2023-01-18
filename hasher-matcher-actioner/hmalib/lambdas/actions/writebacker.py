# Copyright (c) Meta Platforms, Inc. and affiliates.

from hmalib.common.classification_models import WritebackTypes
import json
import os

from hmalib.common.config import HMAConfig
from hmalib.common.logging import get_logger
from hmalib.writebacker.writebacker_base import Writebacker
from hmalib.common.messages.match import BankedSignal
from hmalib.common.messages.writeback import WritebackMessage

logger = get_logger(__name__)


def lambda_handler(event, context):
    """
    This is the main entry point for writing back to ThreatExchange. The action evaluator
    sends a writeback message by way of the writebacks queue and here's where they're
    popped off and dealt with.
    """
    HMAConfig.initialize(os.environ["CONFIG_TABLE_NAME"])

    writebacks_performed = {}
    for sqs_record in event["Records"]:
        # TODO research max # sqs records / lambda_handler invocation
        writeback_message = WritebackMessage.from_aws_json(sqs_record["body"])
        logger.info("Writing Back: %s", writeback_message)

        # get all sources that are related to this writeback
        sources = {
            banked_signal.bank_source
            for banked_signal in writeback_message.banked_signals
        }
        source_writebackers = [
            Writebacker.get_writebacker_for_source(source)
            for source in sources
            if Writebacker.get_writebacker_for_source(source)
        ]
        for writebacker in source_writebackers:
            result = writebacker.perform_writeback(writeback_message)
            logger.info("Writeback result: %s", result)
            writebacks_performed[writebacker.source] = result

    return {"writebacks_performed": writebacks_performed}


if __name__ == "__main__":
    # For basic debugging
    # This will react to real descriptors if WRITEBACK_LOCAL is on
    if os.environ.get("WRITEBACK_LOCAL"):
        writeback_message = WritebackMessage(
            [
                BankedSignal("2915547128556957", "303636684709969", "te"),
            ],
            WritebackTypes.RemoveOpinion,
        )
        event = {"Records": [{"body": writeback_message.to_aws_json()}]}
        result = lambda_handler(event, None)
        print(result)
