import typing as t
from threatexchange.matcher import matcher
from threatexchange.signal_type.index import IndexMatch, SignalTypeIndex
from threatexchange.signal_type.signal_base import SignalType


class HashMatcher(matcher.Matcher[str]):
    def _match_impl(
        self, hash: str, s_type: t.Type[SignalType], index: SignalTypeIndex
    ) -> t.Sequence[IndexMatch]:
        hash = hash.strip()
        if not hash:
            return []
        try:
            hash = s_type.validate_signal_str(hash)
        except:
            # TODO Log exception
            # For now, return empty as we might have a mixed input
            return []
        return index.query(hash)
