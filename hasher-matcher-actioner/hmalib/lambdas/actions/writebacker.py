# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import json

from hmalib.common.logging import get_logger
from hmalib.common.writebacker_models import Writebacker
from hmalib.common.message_models import WritebackMessage

logger = get_logger(__name__)


def lambda_handler(event, context):
    """
    This is the main entry point for writing back to ThreatExchange. The action evaluator
    sends a writeback message by way of the writebacks queue and here's where they're
    popped off and dealt with.
    """
    writebacks_performed = {}
    for sqs_record in event["Records"]:
        # TODO research max # sqs records / lambda_handler invocation
        writeback_message = WritebackMessage.from_aws_json(sqs_record["body"])
        logger.info("Writing Back: %s", writeback_message)

        # get all sources that are related to this writeback
        sources = {
            banked_signal.bank_source
            for banked_signal in writeback_message.matching_banked_signals
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
    pass
