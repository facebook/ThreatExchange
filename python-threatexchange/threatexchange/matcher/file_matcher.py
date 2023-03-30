import pathlib
import typing as t
from threatexchange.matcher import matcher
from threatexchange.signal_type.index import IndexMatch, SignalTypeIndex
from threatexchange.signal_type.signal_base import FileHasher, MatchesStr, SignalType


class FileMatcher(matcher.Matcher[pathlib.Path]):
    def _match_impl(
        self, input: pathlib.Path, s_type: t.Type[SignalType], index: SignalTypeIndex
    ) -> t.Sequence[IndexMatch]:
        if issubclass(s_type, MatchesStr):
            return index.query(input.read_text())
        assert issubclass(s_type, FileHasher)
        return index.query(s_type.hash_from_file(input))
