import typing as t
import os

from functools import lru_cache
from dataclasses import dataclass, fields

from hmalib.common.message_models import BankedSignal, MatchMessage
from hmalib.common.logging import get_logger

from hmalib.common.actioner_models import ActionPerformer
from hmalib.common.label_models import (
    ReactionLabel,
    SawThisTooReactionLabel,
    IngestedReactionLabel,
    FalsePositiveReactionLabel,
    TruePositiveReactionLabel,
)
from hmalib.common.actioner_models import ActionPerformer
from hmalib.common.evaluator_models import ActionLabel
from hmalib.common.message_models import ReactionMessage
from hmalib.aws_secrets import AWSSecrets

from threatexchange.api import ThreatExchangeAPI

logger = get_logger(__name__)


class MockedThreatExchangeAPI:
    mocked_descriptor_ids = ["12345", "67890"]

    def get_threat_descriptors_from_indicator(
        self, indicator
    ) -> t.List[t.Dict[str, str]]:
        return [{"id": id} for id in self.mocked_descriptor_ids]

    def react_to_threat_descriptor(self, descriptor, reaction) -> None:
        assert descriptor in self.mocked_descriptor_ids


class Writebacker:
    """
    For writing back to an HMA data soruce (eg. ThreatExchange). Every source that
    enables writebacks should have an implmentation of this class
    (eg ThreatExchangeWritebacker) and optionally sub implementations
    (eg ThreatExchangeFalsePositiveWritebacker)

    You must also add the subclass you are implementing to the performable_subclasses
    fucntion below
    """

    @property
    def source(self) -> str:
        """
        The source that this writebacker corresponds to (eg. "te")
        """
        raise NotImplementedError

    @staticmethod
    def writeback_options() -> t.Dict[str, t.Type["Writebacker"]]:
        """
        For a given source that performs writebacks, this fucntion specifies what types of
        writebacks that can be taken as a mapping from writback type to writebacker. The
        type should be same as the type of is passed in the WritebackLabel passed to the writebacker
        """
        raise NotImplementedError

    @classmethod
    @lru_cache(maxsize=None)
    def get_writebacker_for_source(cls, source: str) -> t.Optional["Writebacker"]:
        if cls.__name__ != "Writebacker":
            raise ValueError(
                "get_writebacker_for_source can only be called from the Writebacker class directly. eg Writebacker().get_writebacker_for_source"
            )

        print("subclasses", cls.__subclasses__())

        sources_to_writebacker_cls = {
            writebacker_cls().source: writebacker_cls
            for writebacker_cls in cls.__subclasses__()
        }

        if source not in sources_to_writebacker_cls.keys():
            return None
        return sources_to_writebacker_cls[source]()

    def writeback_is_enabled(self) -> bool:
        """
        Users can switch on/off writebacks either globally or for individual sources
        """
        raise NotImplementedError

    @property
    def reaction_label(self) -> ReactionLabel:
        """
        The reaction label for when this action should be performed (eg SawThisTooReactionLabel())
        """
        raise NotImplementedError

    def _writeback_impl(self, writeback_message: ReactionMessage) -> str:
        raise NotImplementedError

    def perform_writeback(self, writeback_message: ReactionMessage) -> str:
        writeback_options = self.writeback_options()
        writeback_to_perform = writeback_message.reaction_label.value
        if writeback_to_perform not in writeback_options:
            return (
                "Could not find writebacker for source "
                + self.source
                + " that can perform writeback "
                + writeback_to_perform
            )

        writebacker = writeback_options[writeback_to_perform]()
        if writebacker.writeback_is_enabled:
            return writebacker._writeback_impl(writeback_message)
        return "Writeback {writebacker.__name__} not performed becuase it switched off"


@dataclass
class ThreatExchangeWritebacker(Writebacker):
    """
    Writebacker parent object for all writebacks to ThreatExchange
    """

    source = "te"

    @staticmethod
    @lru_cache(maxsize=None)
    def writeback_options() -> t.Dict[str, t.Type["Writebacker"]]:
        return {
            "FalsePositive": ThreatExchangeFalsePositiveWritebacker,
            "TruePositive": ThreatExchangeTruePositivePositiveWritebacker,
            "Ingested": ThreatExchangeIngestedWritebacker,
            "SawThisToo": ThreatExchangeSawThisTooWritebacker,
        }

    def writeback_is_enabled(self) -> bool:
        """
        TODO implement
        Looks up from a config whether ThreatExchange reacting is enabled. Initially this will be a global
        config, and this method will return True if reacting is enabled, False otherwise. At some point the
        config for reacting to ThreatExchange may be on a per collaboration basis. In that case, the config
        will be referenced for each collaboration involved (implied by the match message). If reacting
        is enabled for a given collaboration, a label will be added to the match message
        (e.g. "ThreatExchangeReactingEnabled:<collaboration-id>").
        """
        return True

    @property
    def te_api(self) -> ThreatExchangeAPI:
        mock_te_api = os.environ.get("MOCK_TE_API")
        if mock_te_api == "True":
            return MockedThreatExchangeAPI()
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

    def _writeback_impl(self, writeback_message: ReactionMessage) -> str:
        # TODO Implement
        return "Wrote Back false positive"


class ThreatExchangeTruePositivePositiveWritebacker(ThreatExchangeWritebacker):
    """
    For writing back to ThreatExhcnage that the user belives the match was
    correct.

    Executing perform_writeback on this class will read the (indicator, privacy_group)
    pairs for the match and, for each, add a new descriptor on that indicator
    in that privacy group that adds the agreement tag for the privacy group

    """

    def _writeback_impl(self, writeback_message: ReactionMessage) -> str:
        # TODO Implement
        return "Wrote Back true positive"


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

    def _writeback_impl(self, writeback_message: ReactionMessage) -> str:
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
        return (
            "reacted "
            + self.reaction
            + " to "
            + str(len(descriptor_ids))
            + " descriptors"
        )


class ThreatExchangeIngestedWritebacker(ThreatExchangeReactionWritebacker):
    reaction = "INGESTED"


class ThreatExchangeSawThisTooWritebacker(ThreatExchangeReactionWritebacker):
    reaction = "SAW_THIS_TOO"


if __name__ == "__main__":
    pass
