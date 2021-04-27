import typing as t

from dataclasses import dataclass, fields

from hmalib.models import MatchMessage, BankedSignal
from hmalib.common.logging import get_logger
from hmalib.common.actioner_models import ActionPerformer, ActionLabel, ReactionMessage
from hmalib.aws_secrets import AWSSecrets

from threatexchange.api import ThreatExchangeAPI

logger = get_logger(__name__)


@dataclass
class Writebacker(ActionPerformer):
    """
    The action of writing back to an HMA data soruce (eg. ThreatExchange)
    is done through the Action Framework. Every source that enables writebacks
    should have an implmentation of this class (eg ThreatExchangeWritebacker)
    and optionally sub implementations (eg ThreatExchangeFalsePositiveWritebacker)

    You must also add the subclass you are implementing to the performable_subclasses
    fucntion below
    """

    def perform_writeback(self, writeback_message: ReactionMessage) -> None:
        raise NotImplementedError

    def perform_action(self, writeback_message: MatchMessage) -> None:
        if not isinstance(writeback_message, ReactionMessage):
            raise ValueError(
                "You are trying to perform a writeback using {self.__class__} but the argument passed was not a ReactionMessage"
            )
        self.perform_writeback(writeback_message)

    @classmethod
    def performable_subclasses(cls) -> t.List[t.Type["Writebacker"]]:
        return [
            ThreatExchangeFalsePositiveWritebacker,
            ThreatExchangeTruePositivePositiveWritebacker,
            ThreatExchangeInReviewWritebacker,
            ThreatExchangeIngestedWritebacker,
            ThreatExchangeSawThisTooWritebacker,
        ]


@dataclass
class ThreatExchangeWritebacker(Writebacker):
    """
    Common class for writing back to ThreatExchange.
    """

    @property
    def te_api(self) -> ThreatExchangeAPI:
        api_key = AWSSecrets.te_api_key()
        return ThreatExchangeAPI(api_key)


class ThreatExchangeFalsePositiveWritebacker(ThreatExchangeWritebacker):
    """
    For writing back to ThreatExhcnage that the user belives the match was
    a false positive.

    Executing perform_writeback on this class will read the (indicator, privacy_group)
    pairs for the match and, for each, add a new descriptor on that indicator
    in that privacy group that adds the disagreement tag for the privacy group

    """

    def perform_writeback(self, writeback_message: ReactionMessage) -> None:
        # TODO Implement
        pass


class ThreatExchangeTruePositivePositiveWritebacker(ThreatExchangeWritebacker):
    """
    For writing back to ThreatExhcnage that the user belives the match was
    correct.

    Executing perform_writeback on this class will read the (indicator, privacy_group)
    pairs for the match and, for each, add a new descriptor on that indicator
    in that privacy group that adds the agreement tag for the privacy group

    """

    def perform_writeback(self, writeback_message: ReactionMessage) -> None:
        # TODO Implement
        pass


@dataclass
class ThreatExchangeReactionWritebacker(ThreatExchangeWritebacker):
    """
    For writebacks to ThreatExchange that are implemented as reactions.

    Executing perform_writeback on this class will read the indicators
    from the match, load all related descriptors, and write the given reaction
    to them
    """

    @property
    def reaction(self) -> str:
        raise NotImplementedError

    def perform_writeback(self, writeback_message: ReactionMessage) -> None:
        indicator_ids = {
            dataset_match_details.banked_content_id
            for dataset_match_details in writeback_message.matching_banked_signals
            if dataset_match_details.bank_source == "te"
        }

        descriptor_ids = {
            descriptor_id["id"]
            for indicator_id in indicator_ids
            for descriptor_id in self.te_api.get_threat_descriptors_from_indicator(
                indicator_id
            )
        }

        for id in descriptor_ids:
            self.te_api.react_to_threat_descriptor(id, self.reaction)
            logger.info("reacted %s to descriptor %s", self.reaction, id)


class ThreatExchangeInReviewWritebacker(ThreatExchangeReactionWritebacker):
    reaction = "IN_REVIEW"


class ThreatExchangeIngestedWritebacker(ThreatExchangeReactionWritebacker):
    reaction = "INGESTED"


class ThreatExchangeSawThisTooWritebacker(ThreatExchangeReactionWritebacker):
    reaction = "SAW_THIS_TOO"


if __name__ == "__main__":

    banked_signals = [
        BankedSignal("2862392437204724", "bank 4", "te"),
        BankedSignal("4194946153908639", "bank 4", "te"),
    ]
    match_message = MatchMessage("key", "hash", banked_signals)

    configs: t.List[ActionPerformer] = [
        ThreatExchangeIngestedWritebacker("ReactInReview"),
        ThreatExchangeSawThisTooWritebacker(
            "ReactSawThisToo",
        ),
    ]

    # This will react to 4 real descriptors
    for action_config in configs:
        action_config.perform_action(match_message)
