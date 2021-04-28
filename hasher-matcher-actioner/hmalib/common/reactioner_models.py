import typing as t

from dataclasses import dataclass, fields

from hmalib.common.message_models import BankedSignal, MatchMessage
from hmalib.common.logging import get_logger
from hmalib.common.actioner_models import ActionPerformer
from hmalib.common.evaluator_models import ActionLabel
from hmalib.aws_secrets import AWSSecrets

from threatexchange.api import ThreatExchangeAPI

logger = get_logger(__name__)


@dataclass
class ReactActionPerformer(ActionPerformer):
    @property
    def reaction(self) -> str:
        raise NotImplementedError

    def perform_action(self, match_message: MatchMessage) -> None:
        api_key = AWSSecrets.te_api_key()
        api = ThreatExchangeAPI(api_key)

        indicator_ids = {
            dataset_match_details.banked_content_id
            for dataset_match_details in match_message.matching_banked_signals
            if dataset_match_details.bank_source == "te"
        }

        descriptor_ids = {
            descriptor_id["id"]
            for indicator_id in indicator_ids
            for descriptor_id in api.get_threat_descriptors_from_indicator(indicator_id)
        }

        for id in descriptor_ids:
            api.react_to_threat_descriptor(id, self.reaction)
            logger.info("reacted %s to descriptor %s", self.reaction, id)


class ReactInReviewActionPerformer(ReactActionPerformer):
    reaction = "IN_REVIEW"


class ReactIngestedActionPerformer(ReactActionPerformer):
    reaction = "INGESTED"


class ReactSawThisTooActionPerformer(ReactActionPerformer):
    reaction = "SAW_THIS_TOO"


if __name__ == "__main__":

    banked_signals = [
        BankedSignal("2862392437204724", "bank 4", "te"),
        BankedSignal("4194946153908639", "bank 4", "te"),
    ]
    match_message = MatchMessage("key", "hash", banked_signals)

    configs: t.List[ActionPerformer] = [
        ReactInReviewActionPerformer("ReactInReview"),
        ReactSawThisTooActionPerformer(
            "ReactSawThisToo",
        ),
    ]

    # This will react to 4 real descriptors
    for action_config in configs:
        action_config.perform_action(match_message)
