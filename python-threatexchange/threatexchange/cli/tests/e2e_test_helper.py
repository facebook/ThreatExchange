# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved


from io import StringIO
import pathlib
import shutil
import sys
import tempfile
import typing as t
from unittest.mock import patch
import unittest
import pytest

from threatexchange.cli.main import inner_main
from threatexchange.cli.exceptions import CommandError


class E2ETestSystemExit(Exception):
    def __init__(self, code: int) -> None:
        super().__init__()
        self.returncode = code


class ThreatExchangeCLIE2eHelper:

    # A keystroke saver, prefix these args to the beginning
    # of every call.
    # You can bypass by making the first arg "tx" or
    # "threatexchange".
    COMMON_CALL_ARGS: t.Sequence[str] = ()

    _state_dir: pathlib.Path

    def cli_call(self, *given_args: str) -> str:
        """
        Call the threatexchange CLI
        """
        args: t.List[str] = []
        if next(iter(given_args), None) in ("tx", "threatexchange"):
            given_args = given_args[1:]
        else:
            args.extend(self.COMMON_CALL_ARGS)
        args.extend(given_args)
        print("Calling: $ threatexchange", " ".join(args), file=sys.stderr)
        with patch("sys.stdout", new=StringIO(newline=None)) as fake_out, patch(
            "sys.argv", new=["threatexchange"] + args
        ):
            try:
                inner_main(args, state_dir=self._state_dir)
            except SystemExit as se:
                if se.code != 0:
                    raise E2ETestSystemExit(se.code)
            return fake_out.getvalue()

    def assert_cli_output(
        self,
        args: t.Iterable[str],
        expected_output: t.Union[str, t.Iterable[str], t.Dict[int, str]],
    ) -> None:
        output = self.cli_call(*args)
        if isinstance(expected_output, str):
            assert expected_output.strip() == output.strip()
            return
        lines = output.strip().split("\n")
        if not isinstance(expected_output, dict):
            expected_output = dict(enumerate(expected_output))
        for line, expected_line_output in expected_output.items():
            if line < 0:
                assert line >= -len(lines)
            else:
                assert line < len(lines)
            assert lines[line] == expected_line_output

    def assert_cli_usage_error(
        self, args: t.Iterable[str], msg_regex: str = None
    ) -> None:
        with pytest.raises((CommandError, E2ETestSystemExit), match=msg_regex) as ex:
            self.cli_call(*args)
        exception = t.cast(t.Union[CommandError, E2ETestSystemExit], ex.value)
        assert exception.returncode == 2


@pytest.fixture
def te_cli(tmp_path: pathlib.Path) -> ThreatExchangeCLIE2eHelper:
    ret = ThreatExchangeCLIE2eHelper()
    ret._state_dir = tmp_path
    return ret


class ThreatExchangeCLIE2eTest(unittest.TestCase, ThreatExchangeCLIE2eHelper):
    def setUp(self) -> None:
        state_dir = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(str(state_dir)))
        self._state_dir = state_dir
