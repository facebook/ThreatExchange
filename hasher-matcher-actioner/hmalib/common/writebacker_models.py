import typing as t
import os

from functools import lru_cache
from dataclasses import dataclass

from hmalib.common.logging import get_logger
from hmalib.common.classification_models import WritebackTypes
from hmalib.common.message_models import WritebackMessage, BankedSignal
from hmalib.common.fetcher_models import ThreatExchangeConfig
from hmalib.common.mocks import MockedThreatExchangeAPI

from hmalib.aws_secrets import AWSSecrets

from threatexchange.api import ThreatExchangeAPI

logger = get_logger(__name__)

TE_UPLOAD_TAG = "uploaded_by_hma"


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
    def writeback_options() -> t.Dict[
        WritebackTypes.WritebackType, t.Type["Writebacker"]
    ]:
        """
        For a given source that performs writebacks, this fucntion specifies what types of
        writebacks that can be taken as a mapping from writeback type to writebacker. The
        type should be same as WritebackType passed to the writebacker
        """
        raise NotImplementedError

    @classmethod
    @lru_cache(maxsize=None)
    def get_writebacker_for_source(cls, source: str) -> t.Optional["Writebacker"]:
        if cls.__name__ != "Writebacker":
            raise ValueError(
                "get_writebacker_for_source can only be called from the Writebacker class directly. eg Writebacker().get_writebacker_for_source"
            )

        sources_to_writebacker_cls = {
            writebacker_cls().source: writebacker_cls
            for writebacker_cls in cls.__subclasses__()
        }

        if source not in sources_to_writebacker_cls.keys():
            return None
        return sources_to_writebacker_cls[source]()

    def writeback_is_enabled(self, writeback_signal: BankedSignal) -> bool:
        """
        Users can switch on/off writebacks either globally for individual sources, or based on the matched signal
        """
        raise NotImplementedError

    @property
    def writeback_type(self) -> WritebackTypes.WritebackType:
        """
        The writeback label for when this action should be performed (eg WritebackType.SawThisToo)
        """
        raise NotImplementedError

    def _writeback_impl(self, writeback_signal: BankedSignal) -> str:
        raise NotImplementedError

    def perform_writeback(self, writeback_message: WritebackMessage) -> t.List[str]:
        writeback_to_perform = writeback_message.writeback_type

        error = None
        if writeback_to_perform not in self.writeback_options():
            error = (
                "Could not find writebacker for source "
                + self.source
                + " that can perform writeback "
                + writeback_to_perform.value
            )
            logger.error(error)
            return [error]

        results = []
        writebacker = self.writeback_options()[writeback_to_perform]()
        for writeback_signal in writeback_message.banked_signals:
            # filter our matches from other sources
            if writeback_signal.bank_source == self.source:
                result = None
                if writebacker.writeback_is_enabled(writeback_signal):
                    result = writebacker._writeback_impl(writeback_signal)
                else:
                    result = (
                        "No writeback performed for banked content id "
                        + writeback_signal.banked_content_id
                        + " becuase writebacks were disabled"
                    )
                logger.info(result)
                results.append(result)
        return results


@dataclass
class ThreatExchangeWritebacker(Writebacker):
    """
    Writebacker parent object for all writebacks to ThreatExchange
    """

    source = "te"

    @staticmethod
    @lru_cache(maxsize=None)
    def writeback_options() -> t.Dict[
        WritebackTypes.WritebackType, t.Type["Writebacker"]
    ]:
        return {
            WritebackTypes.FalsePositive: ThreatExchangeFalsePositiveWritebacker,
            WritebackTypes.TruePositive: ThreatExchangeTruePositiveWritebacker,
            WritebackTypes.SawThisToo: ThreatExchangeSawThisTooWritebacker,
            WritebackTypes.RemoveOpinion: ThreatExchangeRemoveOpinionWritebacker,
        }

    def writeback_is_enabled(self, writeback_signal: BankedSignal) -> bool:
        privacy_group_id = writeback_signal.bank_id
        privacy_group_config = ThreatExchangeConfig.cached_get(privacy_group_id)
        if isinstance(privacy_group_config, ThreatExchangeConfig):
            return privacy_group_config.write_back
        # If no config, dont write back
        logger.warn("No config found for privacy group " + str(privacy_group_id))
        return False

    @property
    def te_api(self) -> ThreatExchangeAPI:
        mock_te_api = os.environ.get("MOCK_TE_API")
        if mock_te_api == "True":
            return MockedThreatExchangeAPI()
        api_key = AWSSecrets().te_api_key()
        return ThreatExchangeAPI(api_key)


class ThreatExchangeTruePositiveWritebacker(ThreatExchangeWritebacker):
    """
    For writing back to ThreatExhcnage that the user belives the match was
    correct.

    Executing perform_writeback on this class will read the (indicator, privacy_group)
    pairs for the signal and upsert a new descriptor for that indicator with the
    privacy group for this collaboration
    """

    def _writeback_impl(self, writeback_signal: BankedSignal) -> str:
        indicator_id = writeback_signal.banked_content_id
        privacy_group_id = writeback_signal.bank_id
        descriptors = self.te_api.get_threat_descriptors_from_indicator(indicator_id)

        # If we already have a descriptor we can copy it and upload make sure to never expire it
        my_descriptor = None
        for descriptor in descriptors:
            if descriptor["owner"]["id"] == str(self.te_api.app_id):
                my_descriptor = descriptor

        postParams = {
            "privacy_type": "HAS_PRIVACY_GROUP",
            "expire_time": 0,
            "privacy_members": str(privacy_group_id),
            "review_status": "REVIEWED_MANUALLY",
            "status": "MALICIOUS",
        }
        print(descriptors)

        if my_descriptor:
            members = {member for member in my_descriptor.get("privacy_members", [])}

            postParams["privacy_members"] = ",".join(
                members.union({str(privacy_group_id)})
            )
            postParams["descriptor_id"] = my_descriptor["id"]

            # This doesnt actually copy to a new descriptor but acts like an upsert for
            # the properties specified
            response = self.te_api.copy_threat_descriptor(postParams, False, False)
        else:
            postParams["indicator"] = descriptors[0]["indicator"]["indicator"]
            postParams["type"] = descriptors[0]["type"]
            postParams["description"] = "A ThreatDescriptor uploaded via HMA"
            postParams["share_level"] = "RED"
            postParams["tags"] = TE_UPLOAD_TAG

            response = self.te_api.upload_threat_descriptor(postParams, False, False)

        error = response[1] or response[2].get("error", {}).get("message")

        if error:
            return f"""
Error writing back TruePositive for indicator {writeback_signal.banked_content_id}
Error: {error}
""".strip()

        return f"Wrote back TruePositive for indicator {writeback_signal.banked_content_id}\n {'Built' if my_descriptor else 'Updated'} descriptor {response[2]['id']} with privacy groups {postParams['privacy_members']}"


class ThreatExchangeRemoveOpinionWritebacker(ThreatExchangeWritebacker):
    """
    For writing back to ThreatExhcnage that the user belives the match was
    correct.

    Executing perform_writeback on this class will try to remove both
    TruePositive and FalsePositive opinions if they exist.

    To remove a FalsePositive opinion we load the indicator and find all
    associated descriptors. Then, for each indicator, if the user has
    reacted DISAGREE_WITH_TAGS, remove that reaction.

    To remove a TruePositive opinion we need to remove the apps descriptor
    from the collaboration. To do this, we load the (indicator, privacy_group)
    and find a ThreatDescriptor that the user has created for that indicator.
    We then remove the privacy group from that descriptor if it exists thereby
    removing it from the collaboration. If there are no more privacy groups we
    delete the indicator.
    """

    def _writeback_impl(self, writeback_signal: BankedSignal) -> str:
        # TODO Implement
        return (
            f"MOCKED: Removed opinion on indicator {writeback_signal.banked_content_id}"
        )


@dataclass
class ThreatExchangeReactionWritebacker(ThreatExchangeWritebacker):
    """
    For all writebacks to ThreatExchange that are implemented as adding reactions.

    Executing perform_writeback on this class will read the indicators
    from the match, load all related descriptors, and write the given reaction
    to them
    """

    @property
    def reaction(self) -> str:
        raise NotImplementedError

    def _writeback_impl(self, writeback_signal: BankedSignal) -> str:
        indicator_id = writeback_signal.banked_content_id
        descriptors = self.te_api.get_threat_descriptors_from_indicator(indicator_id)
        other_desriptors = [
            d for d in descriptors if d["owner"]["id"] != str(self.te_api.app_id)
        ]
        for descriptor in other_desriptors:
            id = descriptor["id"]
            self.te_api.react_to_threat_descriptor(id, self.reaction)
            logger.info("reacted %s to descriptor %s", self.reaction, id)
        return f"reacted {self.reaction} to {str(len(other_desriptors))} descriptors : {','.join(d['id'] for d in other_desriptors)}"


class ThreatExchangeFalsePositiveWritebacker(ThreatExchangeReactionWritebacker):
    """
    For writing back to ThreatExhcnage that the user belives the match was
    a false positive.
    """

    reaction = "DISAGREE_WITH_TAGS"


# TODO: Currently writing back INGESTED fails becuase of API limits. Need to
#       solve before sending reaction. Possible solution to create new batch react endpoint
# class ThreatExchangeIngestedWritebacker(ThreatExchangeReactionWritebacker):
#     reaction = "INGESTED"


class ThreatExchangeSawThisTooWritebacker(ThreatExchangeReactionWritebacker):
    """
    For writing back to ThreatExhcnage that a Match has occurred
    """

    reaction = "SAW_THIS_TOO"


if __name__ == "__main__":
    pass
