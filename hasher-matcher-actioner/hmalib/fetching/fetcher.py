# Copyright (c) Meta Platforms, Inc. and affiliates.

from functools import lru_cache
import typing as t
import time

from threatexchange.exchanges import auth
from threatexchange.exchanges.collab_config import CollaborationConfigBase
from threatexchange.exchanges.signal_exchange_api import TSignalExchangeAPICls
from threatexchange.exchanges.fetch_state import FetchCheckpointBase, FetchDeltaTyped

from hmalib.common.logging import get_logger
from hmalib.common.mappings import HMASignalTypeMapping, full_class_name
from hmalib.common.models.bank import BanksTable
from hmalib.aws_secrets import AWSSecrets
from hmalib.common.configs import tx_collab_config
from hmalib.common.configs.tx_apis import ToggleableSignalExchangeAPIConfig
from hmalib.fetching.bank_store import BankCollabFetchStore

logger = get_logger(__name__)


class Fetcher:
    """

    In python-threatexchange, SignalExchangeAPI -> CollaborationConfig is
    one-to-many. Which makes sense. An exchange like ThreatExchange can power
    multiple collaborations.

    Even in-house, a single exchange can power multiple collab-like groupings of
    signals.
    """

    def __init__(
        self,
        signal_type_mapping: HMASignalTypeMapping,
        banks_table: BanksTable,
        secrets: AWSSecrets,
    ):
        self.signal_type_mapping = signal_type_mapping
        self.banks_table = banks_table
        self.secrets = secrets

    def _get_api_classes_from_config(self):
        return [
            api.to_concrete_class()
            for api in ToggleableSignalExchangeAPIConfig.get_all()
            if api.enabled
        ]

    def has_hit_limits(self) -> bool:
        return False

    def should_checkpoint(self) -> bool:
        # TBD
        return True
        # if not hasattr(self, "_should_checkpoint_counter"):
        #     self._should_checkpoint_counter = 0

        # self._should_checkpoint_counter = self._should_checkpoint_counter + 1
        # return self._should_checkpoint_counter % 5 == 0

    @lru_cache(maxsize=None)
    def get_api_classes(self) -> t.Dict[str, TSignalExchangeAPICls]:
        """
        Mapping from name to class for all enabled APIs on this HMA instance.
        """
        return {f.get_name(): f for f in self._get_api_classes_from_config()}

    def run(self):
        """
        Lambda will only fire-and-forget into this.

        Any state-management, rate-limiting, time-outing, checkpointing needs to
        happen here.
        """
        all_active_collabs = self._get_all_active_collabs()
        logger.info("Found %d active collaborations.", len(all_active_collabs))
        logger.info(
            "Active signal types are %s",
            [st.get_name() for st in self.signal_type_mapping.signal_types],
        )

        for collab in all_active_collabs:
            self._execute_for_collab(collab)

    def _get_all_active_collabs(
        self,
    ) -> t.List[tx_collab_config.EditableCollaborationConfig]:
        """
        Return all collabs that require fetching in this run.
        """
        return [
            c
            for c in tx_collab_config.get_all_collab_configs()
            if c.to_pytx_collab_config().enabled
        ]

    def _get_credential_string(self, signal_exchange_api_cls: str) -> str:
        api_classes_with_this_exchange = [
            api
            for api in ToggleableSignalExchangeAPIConfig.get_all()
            if api.signal_exchange_api_class == signal_exchange_api_cls
        ]
        assert (
            api_classes_with_this_exchange
        ), f"No SignalExhchange configured for {signal_exchange_api_cls}, but collab config was found."

        return self.secrets.get_secret(
            api_classes_with_this_exchange[0].get_credential_name()
        )

    def get_store(
        self, collab: tx_collab_config.EditableCollaborationConfig
    ) -> BankCollabFetchStore:
        return BankCollabFetchStore(
            self.signal_type_mapping.signal_types, self.banks_table, collab
        )

    def _execute_for_collab(
        self, collab: tx_collab_config.EditableCollaborationConfig
    ) -> bool:
        logger.info("Fetching for collab: %s", collab.name)
        api_cls = self.get_api_classes()[collab.to_pytx_collab_config().api]

        if issubclass(api_cls, auth.SignalExchangeWithAuth):
            creds_class = api_cls.get_credential_cls()
            creds = creds_class._from_str(
                self._get_credential_string(full_class_name(api_cls))
            )
            api_instance = api_cls.for_collab(
                collab=collab.to_pytx_collab_config(), credentials=creds
            )
        else:
            api_instance = api_cls.for_collab(collab=collab.to_pytx_collab_config())

        store = self.get_store(collab)

        checkpoint = store.get_checkpoint()
        if checkpoint:
            logger.info("Found checkpoint: %s", checkpoint)
        else:
            logger.info("No checkpoint found. Will start from scratch.")

        try:
            it = api_instance.fetch_iter(
                self.signal_type_mapping.signal_types, checkpoint=checkpoint
            )
            delta: FetchDeltaTyped
            for delta in it:
                assert delta.checkpoint is not None  # Inifinite loop protection
                logger.info("fetch() with %d new records.", len(delta.updates))
                next_checkpiont = delta.checkpoint

                if checkpoint is not None:
                    prev_time = checkpoint.get_progress_timestamp()
                    progress_time = delta.checkpoint.get_progress_timestamp()

                    if prev_time is not None and progress_time is not None:
                        # A subsequent checkpoint is _before_ a previous checkpoint?
                        assert prev_time <= progress_time, (
                            "checkpoint time rewound? ",
                            "This can indicate a serious ",
                            "problem with the API and checkpointing",
                        )

                checkpoint = next_checkpiont
                store.merge(delta)
                if self.has_hit_limits():
                    # Hit limits. Must checkpoint
                    break
                if self.should_checkpoint():
                    store.flush(checkpoint)
                    self.last_checkpoint_time = time.time()

            # Flush the last delta.
            store.flush(checkpoint)
            completed = True
        except Exception as exc:
            logger.error("Failure during fetch()")
            logger.exception(exc)
            return False
        finally:
            store.flush(checkpoint)

        return True
