# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import json

from hmalib.common.logging import get_logger
from hmalib.common.actioner_models import ReactionMessage
from hmalib.common.reactioner_models import Writebacker

logger = get_logger(__name__)


def lambda_handler(event, context):
    """
    This is the main entry point for reacting to ThreatExchange. The action evaluator
    sends a reaction message by way of the reactions queue and here's where they're
    popped off and dealt with.
    """
    reactions_performed = {}
    for sqs_record in event["Records"]:
        # TODO research max # sqs records / lambda_handler invocation
        reaction_message = ReactionMessage.from_aws_message(sqs_record["body"])

        logger.info("Reacting: reaction_message = %s", reaction_message)

        reaction_label = reaction_message.reaction_label.value

        # get all sources that are related to this reaction
        sources = {
            banked_signal.bank_source
            for banked_signal in reaction_message.matching_banked_signals
        }
        source_writebackers = [
            Writebacker.get_writebacker_for_source(source)
            for source in sources
            if Writebacker.get_writebacker_for_source(source)
        ]
        for writebacker in source_writebackers:
            result = writebacker.perform_writeback(reaction_message)
            reactions_performed[writebacker.source] = result

    return {"reactions_performed": reactions_performed}


if __name__ == "__main__":
    pass
