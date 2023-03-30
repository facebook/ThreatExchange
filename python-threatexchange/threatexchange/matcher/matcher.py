import typing as t

from threatexchange.cli.cli_config import CLISettings
from threatexchange.content_type.content_base import ContentType
from threatexchange.signal_type.index import IndexMatch, SignalTypeIndex
from threatexchange.signal_type.signal_base import SignalType

T = t.TypeVar("T")


class Matcher(t.Generic[T]):
    # question (sa) -- how do we want to handle the settings? In the CLI it's considered
    # a god object -- do we want to pass it to the init of the class?
    def __init__(
        self,
        settings: CLISettings,
        content_type: t.Type[ContentType],
        only_signal: t.Optional[t.Type[SignalType]],
        valid_types: t.Tuple[type, ...],
    ) -> None:
        self.settings = settings
        _signal_types = (
            settings.get_signal_types_for_content(content_type)
            if not only_signal
            else [only_signal]
        )
        self.signal_types = [s for s in _signal_types if issubclass(s, valid_types)]

    def match(self, *input: T) -> t.List[IndexMatch]:
        # TODO -- this is where the fetch command should exist
        indicies = self._get_indicies()
        if not indicies:
            # TODO Logging
            return []
        results: t.List[IndexMatch] = []
        for s_type, index in indicies:
            for i in input:
                results.extend(self._match_impl(i, s_type, index))
        return results

    def _match_impl(
        self, i: T, s_type: t.Type[SignalType], index: SignalTypeIndex
    ) -> t.Sequence[IndexMatch]:
        raise NotImplementedError

    def _get_indicies(self) -> t.List[t.Tuple[t.Type[SignalType], SignalTypeIndex]]:
        indices: t.List[t.Tuple[t.Type[SignalType], SignalTypeIndex]] = []
        for s_type in self.signal_types:
            index = self.settings.index.load(s_type)
            if index is None:
                # TODO logging
                continue
            indices.append((s_type, index))
        return indices
