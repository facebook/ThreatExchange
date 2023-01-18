# Copyright (c) Meta Platforms, Inc. and affiliates.

from functools import reduce
import typing as t

from threatexchange.signal_type.signal_base import SignalType
from threatexchange.exchanges.signal_exchange_api import SignalExchangeAPI
from threatexchange.exchanges.fetch_state import (
    FetchCheckpointBase,
    FetchDelta,
    SignalOpinion,
    TUpdateRecordKey,
    TUpdateRecordValue,
    FetchedSignalMetadata,
)

from hmalib.common.configs.tx_collab_config import EditableCollaborationConfig
from hmalib.common.configs.tx_apis import ToggleableSignalExchangeAPIConfig
from hmalib.common.models.bank import BanksTable
from hmalib.banks import bank_operations as bank_ops
from hmalib.common.logging import get_logger

logger = get_logger(__name__)


class MultipleContentTypesInFetchDeltaRow(Exception):
    """
    At present, we can't handle if a single fetch delta update
    (FetchDelta.updates[]), when passed through
    SignalExchangeAPI.naive_convert_to_signal_type(...) returns signals with
    differing content types.

    Eg. imagine a ncmec id ends up returing an PDQ AND an MD5. We would not know
    which type of bank member to create.

    In the long run, this can be addressed by creating a new content-type eg.
    unavailable which explicitly states that a bank member does not have media
    attached.
    """

    pass


class BankCollabFetchStore:
    """
    Translates fetch operations into bank operations. Ideally, should not need
    to store anything outside of banks.

    Use with a single collab passed when creating an instance. Create multiple
    instances when working with more than one collab.

    References
    ===
    Borrows heavily from python-threatexchange's fetch_cmd.py. fetch_cmd.py and
    bank_store.py together are the strictest users of python-threatexchange's
    SignalExchangeAPI interface methods.

    fetch_cmd stores the fetched data in a SignalExchange specific format
    defined by SignalExchangeAPI's generic typevars. Different
    SignalExchangeAPI's data is later converted into a common type during
    indexing by calling SignalExchangeAPI.naive_convert_to_signal_type.

    bank_store on the other hand, calls naive_convert_to_signal_type at fetch
    time itself and stores data from all SignalExchangeAPIs using a consistent
    API defined by HMA banks and bank-members. Each TUpdateRecordKey in
    SignalExchangeAPI is stored as a bank-member in HMA.

    Another key distinction is what's loaded into memory. fetch_cmd ends up
    loading the entire dataset into memory. In pytx CLI, this is not an issue
    because the data is expected to be co-located on the same computer where
    fetch is running. With HMA, loading the whole bank into memory would be
    time-consuming. So, instead we distill the results of
    SignalExchangeAPI.fetch_value_merge and
    SignalExchagneAPI.naive_convert_to_signal_type calls into updates and
    deletes and issue those commands to the underlying banks.
    """

    def __init__(
        self,
        signal_types: t.Sequence[t.Type[SignalType]],
        banks_table: BanksTable,
        collab: EditableCollaborationConfig,
    ) -> None:
        self.banks_table = banks_table
        self.collab = collab
        self._signal_types = signal_types

        assert (
            collab.import_as_bank_id
        ), f"CollabConfig {collab.name} is not connected to an importable bank. Create a bank, and save again using tx_collab_config apis."
        self._import_bank = banks_table.get_bank(collab.import_as_bank_id)

        pytx_collab = self.collab.to_pytx_collab_config()
        self._api_cls: t.Type[SignalExchangeAPI] = {
            f.get_name(): f
            for f in [
                api.to_concrete_class()
                for api in ToggleableSignalExchangeAPIConfig.get_all()
                if api.enabled
            ]
        }[pytx_collab.api]

        self._unflushed_deletes: t.Set[TUpdateRecordKey] = set()

        # Updates on the same key must get overriden.
        # SignalExchangeAPI.fetch_iter should be returning the entire object.
        # That way we need not keep track of what has changed. Eg.
        # /threat_updates will return all descriptors for an indicator whenever
        # any of those descriptors change.
        self._unflushed_updates: t.MutableMapping[
            TUpdateRecordKey, TUpdateRecordValue
        ] = {}

    def _coerce_key(self, key: TUpdateRecordKey) -> str:
        """
        Convert a FetchDelta update key to a string. This string will be used as
        a bank-member key.

        If for a SignalExchange, the key type is neither str, nor tuple[str,
        str], this function will need updating.
        """
        if type(key) == str:
            return key
        elif type(key) == int:
            return f"{int}"
        elif (
            type(key) == tuple and len(key) == 2 and type(key[0]) == type(key[1]) == str
        ):
            return f"{key[0]}:{key[1]}"
        else:
            raise ValueError(
                "Only str and tuple[str, str] key types supported in BankCollabFetchStore."
            )

    @property
    def _dirty(self) -> bool:
        # Are there unflushed updates?
        return bool(self._unflushed_updates) or bool(self._unflushed_deletes)

    def get_checkpoint(self) -> t.Optional[FetchCheckpointBase]:
        return self.banks_table.get_bank_info(self._import_bank.bank_id)

    def set_checkpoint(self, checkpoint: FetchCheckpointBase):
        return self.banks_table.update_bank_info(self._import_bank.bank_id, checkpoint)

    def merge(self, delta: FetchDelta) -> None:
        """
        Takes each update from `delta.updates` and transforms it using
        fetch_value_merge against an empty update.

        This merged update then is classified into a create/update or a delete
        and stored in the appropriate list in the BankCollabFetchStore instance.

        The lists BankCollabFetchStore._unflushed_updates and _unflushed_deletes
        are then flushed into banks when flush() is called.
        """

        if len(delta.updates) == 0:
            logger.warning("merge() called with no updates for collab %s", self.collab)
            return

        delta_updates = t.cast(
            t.Dict[TUpdateRecordKey, t.Optional[TUpdateRecordValue]], delta.updates
        )

        for update_key, update_value in delta_updates.items():
            # https://github.com/facebook/ThreatExchange/issues/1218
            # NCMECSignalExchangeAPI.fetch_iter() does not return None metadata
            # need to call fetch_value_merge to make that happen. If this is
            # fixed, we can delete the following line.
            update_value = self._api_cls.fetch_value_merge(None, update_value)

            if update_value is None:  # This is a delete.
                self._unflushed_deletes.add(update_key)
                # Why update something if it will end up getting deleted?
                self._unflushed_updates.pop(update_key, None)
            else:  # This update is an add / update
                self._unflushed_updates[update_key] = update_value
                self._unflushed_deletes.discard(update_key)

    def flush(self, checkpoint: FetchCheckpointBase) -> None:
        if self._dirty:
            # self._delta check is avoidable as it is covered by self._dirty,
            # but python type checker gets annoyed.

            del_count = len(self._unflushed_deletes)
            for delete in self._unflushed_deletes:
                self._handle_delete(delete)

            self._unflushed_deletes.clear()
            logger.info(
                "BankCollabFetchStore flushed %d deletes for collab: %s",
                del_count,
                self.collab.name,
            )

            upsert_count = len(self._unflushed_updates)
            for update_key, update_value in self._unflushed_updates.items():
                self._handle_upsert(update_key, update_value)
            self._unflushed_updates = {}
            logger.info(
                "BankCollabFetchStore flushed %d upserts for collab: %s",
                upsert_count,
                self.collab.name,
            )
        else:
            logger.info("FetchStore is clean!")

        if checkpoint:
            logger.info("Setting checkpoint for collab: %s", self.collab.name)
            self.set_checkpoint(checkpoint)
        else:
            logger.warn(
                "No checkpoint found for collab: %s. Next fetch will start at the beginnging of time.",
                self.collab.name,
            )

    def _handle_upsert(self, key: TUpdateRecordKey, value: TUpdateRecordValue):
        """
        Respond to an update event from a signal exchange API. This can happen
        at most once per key per flush.

        A single update can translate into multiple signals, but all will be
        stored as part of the same bank-member.

        If the update when passed through naive_convert_to_signal_type results
        in no signals, it will result in self._handle_delete being called with
        the `key` arg.
        """
        str_key = self._coerce_key(key)

        # Call naive_convert_to_signal_type one update at a time, to get the
        # full expected state of a bank-member.
        signal_type_view = self._api_cls.naive_convert_to_signal_type(
            self._signal_types, self.collab.to_pytx_collab_config(), {key: value}
        )

        if len(signal_type_view) == 0:
            # Cases where none of the signal types in the update can be
            # processed. This should result in a delete.
            #
            # Imagine an exchange returned a phash and a PDQ for an image in the
            # same key. Later, they removed the PDQ hash, but not the phash.
            # Unless we take action here, the PDQ never gets removed from the
            # bank.
            return self._handle_delete(key=key)

        # Ascertain that all signal_types map from the same content type.
        # HMA at present can't store multiple content types in one bank
        # member.
        unique_content_types = {
            # Is there a signal type that may have multiple content_types?
            st.get_content_types()[0]
            for st in signal_type_view.keys()
        }
        if len(unique_content_types) > 1:
            # TODO: https://github.com/facebook/ThreatExchange/issues/1221
            # Support multiple content types returned in a single fetch update
            raise MultipleContentTypesInFetchDeltaRow()

        content_type = unique_content_types.pop()

        opinion_lists = [
            metadata.get_as_opinions()
            for val in signal_type_view.values()
            for metadata in val.values()
        ]
        unique_opinion_tags = set()
        for opinion_list in opinion_lists:
            unique_opinion_tags.update(self.convert_opinions_to_label(opinion_list))

        try:
            member = self.banks_table.add_keyed_bank_member(
                self._import_bank.bank_id,
                str_key,
                content_type,
                None,
                None,
                None,
                "",
                True,
                unique_opinion_tags,
            )
        except KeyError:
            # member already exists, update labels just to be sure.
            member = self.banks_table.update_bank_member(
                self.banks_table._key_for_bank(self._import_bank.bank_id, str_key),
                notes="",
                bank_member_tags=unique_opinion_tags,
            )

        for signal_type in signal_type_view:
            for hash_value in signal_type_view[signal_type].keys():
                self.banks_table.add_bank_member_signal(
                    bank_id=self._import_bank.bank_id,
                    bank_member_id=member.bank_member_id,
                    signal_type=signal_type,
                    signal_value=hash_value,
                )

                # TODO: We don't verify that all existing bank-member signals should continue existing.

    def _handle_delete(self, key: TUpdateRecordKey):
        """
        Respond to a delete from a signal exchange API. Typically, this would
        happen at most once per key per flush.
        """
        str_key = self._coerce_key(key)
        member = self.banks_table.get_keyed_bank_member(
            self._import_bank.bank_id, str_key
        )
        if member:
            bank_ops.remove_bank_member(self.banks_table, member.bank_member_id)

    def convert_opinions_to_label(self, opinions: t.Sequence[SignalOpinion]):
        """
        Simplistic 1:1 translation of opinion tag to label of same name. This
        could be made more configurable on an API / Collab basis via the UI.

        This should be an instance method even though it does not use self. This
        is to ensure that future modifications (that require loading stuff from
        ddb using self.banks_table) can be written.
        """
        return reduce(
            lambda tags, acc: acc.union(tags), map(lambda x: x.tags, opinions), []
        )
