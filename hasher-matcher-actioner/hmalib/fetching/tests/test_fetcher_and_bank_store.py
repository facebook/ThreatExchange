# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Most classes unapologetically stolen from
threatexchange.exchanges.tests.test_state

Verifies (using a mock bank) that the operations issued on a bank when fetching
a collab are what we'd expect.
"""

import typing as t
import contextlib
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
import pytest
import boto3
from moto import mock_dynamodb2

from threatexchange.signal_type.signal_base import SignalType
from threatexchange.exchanges.signal_exchange_api import TSignalExchangeAPICls
from threatexchange.exchanges.collab_config import (
    CollaborationConfigBase,
    CollaborationConfigWithDefaults,
)
from threatexchange.utils.dataclass_json import dataclass_dumps
from threatexchange.exchanges.signal_exchange_api import SignalExchangeAPI
from threatexchange.exchanges.fetch_state import (
    FetchCheckpointBase,
    TUpdateRecordKey,
    TUpdateRecordValue,
    SignalOpinion,
    SignalOpinionCategory,
    FetchedSignalMetadata,
    FetchDelta,
)
from threatexchange.signal_type.md5 import VideoMD5Signal
from threatexchange.signal_type.pdq.signal import PdqSignal
from threatexchange.content_type.text import TextContent
from threatexchange.content_type.content_base import ContentType

from hmalib.aws_secrets import AWSSecrets
from hmalib.fetching.fetcher import Fetcher
from hmalib.fetching.bank_store import BankCollabFetchStore
from hmalib.common.mappings import HMASignalTypeMapping
from hmalib.common.models.bank import (
    BanksTable,
    Bank,
    BankMember,
    BankMemberSignal,
    PaginatedResponse,
)
from hmalib.common.config import HMAConfig, create_config
from hmalib.common.configs.tx_collab_config import EditableCollaborationConfig
from hmalib.common.configs.tx_apis import ToggleableSignalExchangeAPIConfig

from hmalib.common.tests.mapping_common import get_default_signal_type_mapping
from hmalib.common.models.tests.ddb_test_common import (
    DynamoDBTableTestBase,
    HMAConfigTestBase,
)
from hmalib.common.models.tests.test_signal_uniqueness import BanksTableTestBase


@dataclass
class FakeCheckpoint(FetchCheckpointBase):
    update_time: int


@dataclass
class FakeUpdateRecord:
    # Interpret all values None as delete
    signal_type: t.Optional[t.Type[SignalType]]
    signal_value: t.Optional[str]
    tag: t.Optional[str]


@dataclass
class FakeSignalMetadata(FetchedSignalMetadata):
    tags: t.Set[str]

    def get_as_opinions(self) -> t.Sequence[SignalOpinion]:
        return [
            SignalOpinion(True, SignalOpinionCategory.INVESTIGATION_SEED, self.tags)
        ]


class ImaginarySignalType(SignalType):
    @classmethod
    def get_content_types(cls) -> t.List[t.Type[ContentType]]:
        return [TextContent]


class FakeAPI(
    SignalExchangeAPI[
        CollaborationConfigBase,
        FakeCheckpoint,
        FakeSignalMetadata,
        str,
        FakeUpdateRecord,
    ]
):

    # Since FakeAPI is instantiated via a classmethod and FakeAPI needs to be
    # discoverable as hmalib.foo.bar.tests.FakeAPI, I can't use any kind of
    # dynamic class gen.
    fetch_responses: t.ClassVar[
        t.Sequence[t.Dict[TUpdateRecordKey, t.Optional[TUpdateRecordValue]]]
    ] = []

    @classmethod
    def for_collab(cls, collab: CollaborationConfigBase) -> SignalExchangeAPI:
        return FakeAPI()

    def fetch_iter(
        self,
        supported_signal_types: t.Sequence[t.Type[SignalType]],
        checkpoint: t.Optional[FakeCheckpoint],
    ) -> t.Iterator[FetchDelta[str, FakeUpdateRecord, FakeCheckpoint]]:
        for i, update in enumerate(self.__class__.fetch_responses):
            yield FetchDelta(update, FakeCheckpoint((i + 1) * 100))

    @staticmethod
    def get_config_cls() -> t.Type[CollaborationConfigBase]:
        return CollaborationConfigBase

    @staticmethod
    def get_checkpoint_cls() -> t.Type[FakeCheckpoint]:
        return FakeCheckpoint

    @staticmethod
    def get_record_cls() -> t.Type[FakeSignalMetadata]:
        return FakeSignalMetadata

    @classmethod
    def naive_convert_to_signal_type(
        cls,
        signal_types: t.Sequence[t.Type[SignalType]],
        collab: CollaborationConfigBase,
        fetched: t.Mapping[int, t.Optional[FakeUpdateRecord]],
    ) -> t.Dict[t.Type[SignalType], t.Dict[str, FakeSignalMetadata]]:
        result: t.Dict[t.Type[SignalType], t.Dict[str, t.Set[str]]] = defaultdict(
            lambda: defaultdict(set)
        )
        for update in fetched.values():
            if (
                update is not None
                and update.signal_type is not None
                and update.signal_value is not None
                and update.tag is not None
            ):
                if update.signal_type in signal_types:
                    result[update.signal_type][update.signal_value].add(update.tag)

        return {
            k: {ik: FakeSignalMetadata(iv) for ik, iv in v.items()}
            for k, v in result.items()
        }


class FakeFetcher(Fetcher):
    """
    Allows overriding store. Since the real fetcher must instantiate a store per
    collab, we need this override.
    """

    def __init__(
        self,
        signal_type_mapping: HMASignalTypeMapping,
        banks_table: BanksTable,
        store: BankCollabFetchStore,
    ):
        super().__init__(signal_type_mapping, banks_table, AWSSecrets(""))
        self._fake_store = store

    def get_store(self, collab: EditableCollaborationConfig) -> BankCollabFetchStore:
        return self._fake_store


@pytest.fixture
def banks_table():
    DynamoDBTableTestBase.mock_aws_credentials()
    mddb = mock_dynamodb2()
    mddb.start()
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    # Create the config table too, just in case a table needs it. Would be best
    # if we could somehow make config_table a fixture too, but using mocked
    # dynamodb would have become unwieldy.
    dynamodb.create_table(**HMAConfigTestBase.get_table_definition())
    HMAConfig.initialize(HMAConfigTestBase.TABLE_NAME)

    table = dynamodb.create_table(**BanksTableTestBase.get_table_definition())
    yield BanksTable(table, get_default_signal_type_mapping())
    mddb.stop()


@pytest.fixture
def mock_enabled_signal_exchange_apis(monkeypatch):
    def mock_get(*args, **kwargs):
        return [
            ToggleableSignalExchangeAPIConfig(
                "fake",
                "hmalib.fetching.tests.test_fetcher_and_bank_store.FakeAPI",
                True,
            )
        ]

    monkeypatch.setattr(ToggleableSignalExchangeAPIConfig, "get_all", mock_get)


def get_fake_collab_config(import_as_bank_id: str) -> CollaborationConfigBase:
    pytx_config = CollaborationConfigWithDefaults("Test State", "fake")  # type: ignore

    return EditableCollaborationConfig(
        name="does not matter",
        collab_config_class="threatexchange.exchanges.collab_config.CollaborationConfigWithDefaults",
        attributes_json_serialized=dataclass_dumps(pytx_config),
        import_as_bank_id=import_as_bank_id,
    )


# For brevity when describing test cases.
K1 = "key-one"
K2 = "key-two"
K3 = "key-three"


def md5(n: int) -> str:
    return f"{n:032x}"


def pdq(n: int) -> str:
    return f"{n:064x}"


# Each test case is a 3 [or 4] value tuple. For each case n,
# tuple[0] is a human readable test name. We'll print this if tests fail.
# tuple[1] is the update to be emitted by fetch_iter()
# tuple[2] is the expected end state after all n tuple[1]s have been emitted.
# tuple[3] if NotImplemented, indicates unsupported behavior. Unsupported means
# a missing feature that is not catastrophic but should be addressed soon. An
# example is fetch_iter K1 [PDQ] followed by K1 [PDNA] will not remove the PDQ.
#
# Note: the test cases are cumulative. Each test case will behave as if all the
# previous tests have been performed on this store.
TEST_CASES = [
    (
        "Must have no indexable content when naive_convert_to_signal_type returns None",
        {K1: FakeUpdateRecord(ImaginarySignalType, md5(1), "tag-one")},
        {},
    ),
    (
        "Must have one indexable signal for one known signal type.",
        {K1: FakeUpdateRecord(VideoMD5Signal, md5(1), "tag-one")},
        {VideoMD5Signal: {md5(1)}},
    ),
    (
        "Must be able to replace signals of same key..",
        {
            K1: FakeUpdateRecord(VideoMD5Signal, md5(2), "tag-two"),
            K2: FakeUpdateRecord(VideoMD5Signal, md5(3), "tag-three"),
        },
        {VideoMD5Signal: {md5(3)}},
        NotImplemented,
    ),
    (
        "Must be able to handle a delete for a known key.",
        {K1: None},
        {VideoMD5Signal: {md5(3)}},
    ),
]


def unwrap_bank_signals_response(response: PaginatedResponse) -> t.Set[str]:
    """
    Helper to convert bank member signals response to something that can be
    compared with TEST_CASE data
    """
    return {item.signal_value for item in response.items}


@pytest.mark.usefixtures(
    "mock_enabled_signal_exchange_apis",
)
@pytest.mark.parametrize("i", range(len(TEST_CASES)))
def test_for_case_until(i, banks_table):
    signal_type_mapping = get_default_signal_type_mapping()
    bank = banks_table.create_bank("TEST_IMPORT_COLLAB", "Description")

    fake_config = get_fake_collab_config(bank.bank_id)
    create_config(fake_config)

    FakeAPI.fetch_responses = [tc[1] for tc in TEST_CASES[: i + 1]]

    fetch_store = BankCollabFetchStore(
        signal_type_mapping.signal_types, banks_table, fake_config
    )
    fetcher = FakeFetcher(signal_type_mapping, banks_table, fetch_store)
    fetcher.run()

    for signal_type, signal_values in TEST_CASES[i][2].items():
        context = (
            pytest.raises(AssertionError)
            if NotImplemented in TEST_CASES[i]
            else contextlib.nullcontext()
        )

        with context:
            assert (
                unwrap_bank_signals_response(
                    banks_table.get_bank_member_signals_to_process_page(signal_type)
                )
                == signal_values
            ), TEST_CASES[i][0]
