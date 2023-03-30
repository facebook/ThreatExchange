import pathlib
import typing as t
from threatexchange.cli.cli_config import CLISettings

from threatexchange.content_type.content_base import ContentType
from threatexchange.signal_type.signal_base import FileHasher, SignalType


class Hasher:
    def __init__(
        self,
        settings: CLISettings,
        content_type: t.Type[ContentType],
        signal_type: t.Optional[t.Type[SignalType]],
    ) -> None:
        self.hashers = [
            s
            for s in settings.get_signal_types_for_content(content_type)
            if issubclass(s, FileHasher)
        ]
        if signal_type:
            if signal_type not in self.hashers:
                raise ValueError(
                    f"{self.signal_type.get_name()} "
                    f"does not apply to {self.content_type.get_name()}"
                )
            self.hashers = [signal_type]

    def hash(self, *files: pathlib.Path) -> t.List[str]:
        resp : t.List[str] = []
        for file in files:
            for hasher in self.hashers:
                hash_str = hasher.hash_from_file(file)
                if hash_str:
                    resp.append(hasher.get_name() + " " + hash_str)
        return resp