# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

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
from hmalib.common.logging import get_logger

logger = get_logger(__name__)


class NoImportAsBankDefined(Exception):
    def __init__(self, collab_config: EditableCollaborationConfig):
        self.collab_config = collab_config
        super().__init__(
            f"CollabConfig {collab_config.name} is not connected to an importable bank. Create a bank, and save again using tx_collab_config apis."
        )


class MultipleContentTypesInFetchDeltaRow(Exception):
    pass


class BankCollabFetchStore:
    """
    Translates fetch operations into bank operations. Ideally, should not need
    to store anything outside of banks.

    Use with a single collab passed when creating an instance. Create multiple
    instances when working with more than one collab.
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

        try:
            self._import_bank = banks_table.get_bank(collab.import_as_bank_id)
        except Exception:
            logger.error(f"No bank configured for exporting collab: {collab.name}")
            raise NoImportAsBankDefined(collab_config=collab)

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
        return len(self._unflushed_updates) != 0 or len(self._unflushed_deletes) != 0

    def get_checkpoint(self) -> t.Optional[FetchCheckpointBase]:
        return self.banks_table.get_bank_info(self._import_bank.bank_id)

    def set_checkpoint(self, checkpoint: FetchCheckpointBase):
        return self.banks_table.update_bank_info(self._import_bank.bank_id, checkpoint)

    def merge(self, delta: FetchDelta) -> None:
        """
        David's suggestion was:
        1. try to merge updates one at a time to determine what get's added,
        what gets deleted.
        2. SignalExchangeAPI.naive_fetch_merge is considered demonstration only
        and should not be used here.

        NCMEC FetchDelta.updates key
        - entry.member_id-entry.id -> multiple hashes...
        StopNCII, FBThreatExchange FetchDelta.updates key
        - hash-type, hash-value
        """

        if len(delta.updates) == 0:
            logger.warning("merge() called with no updates")
            return

        delta_updates = t.cast(
            t.Dict[TUpdateRecordKey, t.Optional[TUpdateRecordValue]], delta.updates
        )

        for update_key, update_value in delta_updates.items():
            # NCMECSignalExchangeAPI.fetch_iter() does not clear metadata,
            # need to call fetch_value_merge to clear metadata.
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

            del_count = 0
            while len(self._unflushed_deletes) > 0:
                delete = self._unflushed_deletes.pop()
                self._handle_delete(delete)
                del_count = del_count + 1
            logger.info(
                "BankCollabFetchStore flushed %d deletes for collab: %s",
                del_count,
                self.collab.name,
            )

            upsert_count = 0
            for update_key in list(self._unflushed_updates.keys()):
                update_value = self._unflushed_updates.pop(update_key)
                self._handle_upsert(update_key, update_value)
                upsert_count = upsert_count + 1
            logger.info(
                "BankCollabFetchStore flushed %d upserts for collab: %s",
                upsert_count,
                self.collab.name,
            )
        else:
            logger.info("FetchStore is clean!")

        logger.info("Setting checkpoint for collab: %s", self.collab.name)
        self.set_checkpoint(checkpoint)

    def clear(self) -> None:
        """
        This one might be a time-consuming operation.

        The ideal way would be to get a list of all bank members and then remove
        them and their signals. However, that would have to rely on paginated
        queries and batch operations which are both slow in dynamodb.

        An easier way out would be to iterate over all collab configs, unlink
        their banks and then
        """
        raise NotImplementedError

    def _handle_upsert(self, key: TUpdateRecordKey, value: TUpdateRecordValue):
        """
        Respond to an update event from a signal exchange API. This can happen
        at most once per key per flush.

        A single update can translate into multiple signals, but all will be
        stored as part of the same bank-member.
        """
        str_key = self._coerce_key(key)

        # Call naive_convert_to_signal_type one update at a time, to get the
        # full expected state of a bank-member.
        signal_type_view = self._api_cls.naive_convert_to_signal_type(
            self._signal_types, self.collab.to_pytx_collab_config(), {key: value}
        )

        if len(signal_type_view) == 0:
            # Cases where none of the signal types in the update can be
            # processed. eg. NCMEC returning pdna
            return

        # Ascertain that all signal_types map from the same content type.
        # HMA at present can't store multiple content types in one bank
        # member.
        unique_content_types = set(
            # Is there a signal type that may have multiple content_types?
            list(map(lambda st: st.get_content_types()[0], signal_type_view.keys()))
        )
        if len(unique_content_types) > 1:
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
            self.banks_table.remove_bank_member(member.bank_member_id)

    def convert_opinions_to_label(self, opinions: t.Sequence[SignalOpinion]):
        """
        Simplistic 1:1 translation of opinion tag to label of same name. This
        could be made more configurable on an API / Collab basis via the UI.

        This should be an instance method even though it does not use self. This
        is to ensure that future modifications (that require loading stuff from
        ddb using self.banks_table) can be written.
        """
        return reduce(
            lambda tags, acc: acc.union(tags), map(lambda x: x.tags, opinions)
        )
