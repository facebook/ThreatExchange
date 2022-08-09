# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
The SignalExchangeAPI talks to external APIs to read/write signals

@see SignalExchangeAPI
"""

from abc import ABC, ABCMeta, abstractmethod
import contextlib
import logging
import os
import pathlib
import typing as t

from threatexchange import common
from threatexchange.exchanges.collab_config import CollaborationConfigBase
from threatexchange.signal_type.signal_base import SignalType
from threatexchange.exchanges import fetch_state as state

TCollabConfig = t.TypeVar("TCollabConfig", bound=CollaborationConfigBase)


class SignalExchangeAPI(
    t.Generic[
        TCollabConfig,
        state.TFetchCheckpoint,
        state.TFetchedSignalMetadata,
        state.TUpdateRecordKey,
        state.TUpdateRecordValue,
    ],
    ABC,
):
    """
    APIs to read and maybe write signals.

    SignalExchangeAPIs should checkpoint their progress, so that they
    can tail updates. If this is not possible, they can instead use
    checkpoints to record how long it has been since a full fetch, and
    trigger a refresh if a certain amount of time has passed.

    While this interface is primarily intended for connecting with
    externally hosted servers, it might be useful to write adopters for
    certain formats of local files, which could be valuable for testing.

    Is assumed that fetched signals have some metadata attached to them,
    which is unique to that API. Additionally, it a assumed that there
    might be multiple contributors (owners) to signals inside of an API.

    An instance of this class can retain state (caching connecting, etc)
    as needed, and objects may be persisted to fetch multiple configs.

    = On fetch_iter() returns =
    In order to efficiently store state, it's assumed that data pulled from
    the API can be partitioned in some way by key. If this doesn't make sense
    for your API, or it's mostly a toy implementation, empty string is a
    valid key, and the value can be the entire dataset.

    = On Authentification =
    It's expected that an instance of the class is fully authenticated,
    and in general, auth should be passible by the constructor.

    If an API is constructed via the for_collab classmethod constructor,
    it should attempt to authenticate itself via discovering it from the
    execution environment and passing it via __init__(). If constructed
    directly, it should not search for credentials.

    """

    @classmethod
    @abstractmethod
    def for_collab(cls, collab: TCollabConfig) -> "SignalExchangeAPI":
        """
        An alternative constructor to get a working instance of the API.

        An instance provided by this class is expected to:
        1. Be fully authenticated or throw an exception
        2. All methods are callable if supported by the base implementation

        For implementations that do need additional configuration or
        authentification, this method is a good place to attempt to pull in
        default authentification from known locations. Your general options
        are:
        1. From an environment variable
        2. From a file in a known location (ideally chmod 400)
        3. From a keychain service or similar running in the background
        4. From the collaboration config itself

        If you aren't able to get required authentification, it's best to
        include what options a user has in the exception - even if that's
        just a link to the README.

        Don't:
        * Prompt the user via stdin
        * Return an instance that will throw when any methods are called

        Usages of this library will only attempt to instanciate an API
        when they have an API call to make - all methods for manipulating
        local state are classmethods.
        """
        raise NotImplementedError

    @classmethod
    def get_name(cls) -> str:
        """
        A simple string name unique to SignalExchangeAPIs in use.

        It should be one lowercase_with_underscores word.

        This shouldn't be changed once comitted, or you may break naive
        storage solutions (like the one in the CLI) which stores fetched
        data by (SignalExchangeAPI.name(), collab_name).
        """
        name = cls.__name__
        for suffix in ("API", "Exchange"):
            if name.endswith(suffix):
                name = name[: -len(suffix)]
        return common.class_name_to_human_name(name, "Signal")

    @classmethod
    def get_checkpoint_cls(cls) -> t.Type[state.TFetchCheckpoint]:
        """Returns the dataclass used to control checkpoint for this API"""
        # Default = no checkpoints
        return state.FetchCheckpointBase  # type: ignore

    @classmethod
    def get_record_cls(cls) -> t.Type[state.TFetchedSignalMetadata]:
        """Returns the dataclass used to store records for this API"""
        # Default = no metadata
        return state.FetchedSignalMetadata  # type: ignore

    @classmethod
    def get_config_class(cls) -> t.Type[TCollabConfig]:
        """Returns the dataclass used to store records for this API"""
        # Default - just knowing the type is enough
        return CollaborationConfigBase  # type: ignore

    @classmethod
    def fetch_value_merge(
        cls,
        old: t.Optional[state.TUpdateRecordValue],
        new: t.Optional[state.TUpdateRecordValue],  # can be modified in-place
    ) -> t.Optional[state.TUpdateRecordValue]:
        """
        Merge a new update produced by fetch.

        Returning a value of None indicates that the entry should be deleted.

        Most implementations will probably prefer the default, which is to
        replace the record entirely.

        It is safe to mutate `new` inline and return it, if needed.
        """
        # Default implementation is replace
        return new

    @classmethod
    @t.final
    def naive_fetch_merge(
        cls,
        old: t.Dict[
            state.TUpdateRecordKey, state.TUpdateRecordValue
        ],  # modified in place
        new: t.Mapping[state.TUpdateRecordKey, t.Optional[state.TUpdateRecordValue]],
    ) -> None:
        """
        Merge the results of a fetch in-memory.

        This implementation is mostly for demonstration purposes and testing,
        since even simple usecases may prefer to avoid loading the whole dataset
        in memory and merging by key.

        For example, if you have nothing else, merging NCMEC update records
        together keyed by ID will eventually get you an entire copy of the database.
        """
        for k, v in new.items():
            new_v = cls.fetch_value_merge(old.get(k), v)
            if new_v is None:
                old.pop(k, None)  # type: ignore
            else:
                old[k] = new_v

    @classmethod
    @abstractmethod
    def naive_convert_to_signal_type(
        cls,
        signal_types: t.Sequence[t.Type[SignalType]],
        collab: TCollabConfig,
        fetched: t.Mapping[state.TUpdateRecordKey, state.TUpdateRecordValue],
    ) -> t.Dict[t.Type[SignalType], t.Dict[str, state.TFetchedSignalMetadata]]:
        """
        Convert the record from the API format to the format needed for indexing.

        This is the fallback method of creating state when there isn't a
        specialized storage for the fetch type.

        """
        raise NotImplementedError

    @abstractmethod
    def fetch_iter(
        self,
        supported_signal_types: t.Sequence[t.Type[SignalType]],
        # None if fetching for the first time,
        # otherwise the previous FetchDelta returned
        checkpoint: t.Optional[state.TFetchCheckpoint],
    ) -> t.Iterator[
        state.FetchDelta[
            state.TUpdateRecordKey, state.TUpdateRecordValue, state.TFetchCheckpoint
        ]
    ]:
        """
        Call out to external resources, fetching a batch of updates per yield.

        Many APIs are a sequence of events: (creates/updates, deletions)
        In that case, it's important the these events are strictly ordered.
        I.e. if the sequence is create => delete, if the sequence is reversed
        to delete => create, the end result is a stored record, when the
        expected is a deleted one.

        Updates are assumed to have a keys that can partition the dataset. See the
        note on this in the class docstring.

        The iterator may be abandoned before it is completely exhausted.

        If the iterator returns, it should be because there is no more data
        (i.e. the fetch is up to date).
        """
        raise NotImplementedError

    # TODO - Restore in a future version
    # def report_seen(
    #     self,
    #     collab: TCollabConfig,
    #     s_type: SignalType,
    #     signal: str,
    #     metadata: state.TFetchedSignalMetadata,
    # ) -> None:
    #     """
    #     Report that you observed this signal.

    #     This is an optional API, and places that use it should catch
    #     the NotImplementError.
    #     """
    #     raise NotImplementedError

    def report_opinion(
        self,
        s_type: t.Type[SignalType],
        signal: str,
        opinion: state.SignalOpinion,
    ) -> None:
        """
        Weigh in on a signal for this collaboration.

        Most implementations will want a full replacement specialization, but this
        allows a common interface for all uploads for the simplest usecases.

        This is an optional API, and places that use it should catch
        the NotImplementError.
        """
        raise NotImplementedError


# A convenience helper since mypy can't intuit that bound != t.Any
# For methods like get_checkpoint_cls
TSignalExchangeAPI = SignalExchangeAPI[
    CollaborationConfigBase,
    state.FetchCheckpointBase,
    state.FetchedSignalMetadata,
    t.Any,
    t.Any,
]

TSignalExchangeAPICls = t.Type[TSignalExchangeAPI]


class SignalExchangeAPIWithSimpleUpdates(
    SignalExchangeAPI[
        TCollabConfig,
        state.TFetchCheckpoint,
        state.TFetchedSignalMetadata,
        t.Tuple[str, str],
        state.TFetchedSignalMetadata,
    ]
):
    """
    An API that conveniently maps directly into the form needed by index.

    If the API supports returning exactly the hashes and all the metadata needed
    to make a decision on the hash without needing an indirection of ID (for example,
    to support deletes), then you can choose to directly return it in a form that
    maps directly into SignalType.
    """

    @classmethod
    def naive_convert_to_signal_type(
        cls,
        signal_types: t.Sequence[t.Type[SignalType]],
        collab: TCollabConfig,
        fetched: t.Mapping[t.Tuple[str, str], t.Optional[state.TFetchedSignalMetadata]],
    ) -> t.Dict[t.Type[SignalType], t.Dict[str, state.TFetchedSignalMetadata]]:
        ret: t.Dict[t.Type[SignalType], t.Dict[str, state.TFetchedSignalMetadata]] = {}
        type_by_name = {st.get_name(): st for st in signal_types}
        for (type_str, signal_str), metadata in fetched.items():
            s_type = type_by_name.get(type_str)
            if s_type is None or metadata is None:
                continue
            inner = ret.get(s_type)
            if inner is None:
                inner = {}
                ret[s_type] = inner
            inner[signal_str] = metadata
        return ret


class SignalExchangeAPIInvalidAuthException(Exception):
    """
    An exception you can use to hint users their authentification is bad

    This can be because it's incorrectly formatted, it's been expired,
    or a multitude of other reasons.
    """

    def __init__(self, src_api: t.Type[SignalExchangeAPI], message: str) -> None:
        self.src_api = src_api
        self.message = message


class SignalExchangeAPIMissingAuthException(Exception):
    """
    An exception you can use to hint users how to authentificate your API
    """

    def __init__(
        self,
        src_api: t.Type[SignalExchangeAPI],
        *,
        file_hint: str = "",
        env_hint: str = "",
    ) -> None:
        self.src_api = src_api
        self.hints: t.List[str] = []
        if env_hint:
            self.add_env_hint(env_hint)
        if file_hint:
            self.add_file_hint(file_hint)

    def add_file_hint(self, filename: str) -> None:
        self.hints.append(
            f"creating (and maybe `chmod 400`) a file with credentials at {filename}"
        )

    def add_env_hint(self, variable_name: str) -> None:
        self.hints.append(f"populating an environment variable called {variable_name}")

    def pretty_str(self) -> str:
        lines = [
            f"Couldn't authenticate {self.src_api.get_name()}, "
            "it's missing authentification!"
        ]
        if self.hints:
            lines.append("You can fix this by:")
            for i, hint in enumerate(self.hints, 1):
                lines.append(f"  {i}. {hint}")
        return "\n".join(lines)


CredentialSelf = t.TypeVar("CredentialSelf", bound="CredentialHelper")


class CredentialHelper:
    """
    Wrapper to help standardize credential sources, and tie to exceptions
    """

    ENV_VARIABLE: t.ClassVar[str] = ""
    FILE_NAME: t.ClassVar[str] = ""

    # This is slated to be removed in a future version!
    # It's a placeholder approach while for_collab() gains the auth argument
    _DEFAULT: t.ClassVar[t.Optional["CredentialHelper"]] = None  # t.Self
    _DEFAULT_SRC: t.ClassVar[str] = ""

    @classmethod
    def get(
        cls: t.Type[CredentialSelf], for_cls: t.Type[SignalExchangeAPI]
    ) -> CredentialSelf:
        srcs: t.List[t.Tuple[t.Callable[[], t.Optional[CredentialSelf]], str]] = [
            ((lambda: cls._DEFAULT), cls._DEFAULT_SRC),  # type: ignore[list-item,return-value]
            (cls._from_env, f"environment variable {cls.ENV_VARIABLE}"),
            (cls._from_file, f"file {cls.FILE_NAME}"),
        ]
        for fn, src in srcs:
            try:
                creds = fn()
                if creds is None:
                    continue
                if creds._are_valid():
                    return creds
            except Exception:
                logging.exception("Exception during parsing %s", src)
                pass
            raise SignalExchangeAPIInvalidAuthException(
                for_cls, f"Invalid credentials from {src}"
            )
        ex = SignalExchangeAPIMissingAuthException(for_cls)
        if cls._DEFAULT_SRC:
            ex.hints.append(cls._DEFAULT_SRC)
        if cls.ENV_VARIABLE:
            ex.add_env_hint(cls.ENV_VARIABLE)
        if cls.FILE_NAME:
            ex.add_file_hint(cls.FILE_NAME)
        raise ex

    @classmethod
    def set_default(
        cls: t.Type[CredentialSelf], new_default: t.Optional[CredentialSelf], src: str
    ) -> contextlib.AbstractContextManager:
        """
        Set the default (highest preferred) credentials manually.

        They won't be checked for validity until a future get()

        This call can be used as contextmanager to unset within a `with` statement
        """
        cls._DEFAULT = new_default  # type: ignore[assignment]  # need t.Self
        cls._DEFAULT_SRC = src
        return cls._unset_default_context()

    @classmethod
    @contextlib.contextmanager
    def _unset_default_context(cls: t.Type[CredentialSelf]) -> t.Iterator[None]:
        yield
        cls.clear_default()

    @classmethod
    def clear_default(cls) -> None:
        """Reset the default"""
        cls.set_default(None, "")

    @classmethod
    def _from_str(cls: t.Type[CredentialSelf], s: str) -> t.Optional[CredentialSelf]:
        """Parse credentials from a string"""
        return None

    @classmethod
    def _from_file(cls: t.Type[CredentialSelf]) -> t.Optional[CredentialSelf]:
        """Parse credentials from a file"""
        if not cls.FILE_NAME:
            return None
        path = pathlib.Path(cls.FILE_NAME).expanduser()
        if not path.is_file():
            return None
        return cls._from_str(path.read_text().strip())

    @classmethod
    def _from_env(cls: t.Type[CredentialSelf]) -> t.Optional[CredentialSelf]:
        """Parse credentials from an environment variable"""
        if not cls.ENV_VARIABLE:
            return None
        s = os.environ.get(cls.ENV_VARIABLE)
        if not s:
            return None
        return cls._from_str(s)

    def _are_valid(self) -> bool:
        return True
