# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved


from io import StringIO
import math
import pathlib
import shutil
import sys
import tempfile
import typing as t
from unittest.mock import patch
import unittest

from threatexchange.cli.main import main
from threatexchange.cli.exceptions import CommandError


class E2ETestSystemExit(Exception):
    def __init__(self, code: int) -> None:
        self.returncode = code


class ThreatExchangeCLIE2eTest(unittest.TestCase):

    COMMON_CALL_ARGS: t.ClassVar[t.Sequence[str]] = ()

    _state_dir: pathlib.Path

    def setUp(self) -> None:
        super().setUp()

        state_dir = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(str(state_dir)))
        self._state_dir = state_dir

    def cli_call_helper(self, std_op: str, *given_args: str) -> str:
        args = list(self.COMMON_CALL_ARGS)
        args.extend(given_args)
        print("Calling: $ threatexchange", " ".join(args), file=sys.stderr)
        try:
            with patch(std_op, new=StringIO()) as fake_out:
                main(args, state_dir=self._state_dir)
            return fake_out.getvalue()
        except SystemExit as se:
            if se.code == 0:  # ERROR: Everything is fine
                return fake_out.getvalue()
            raise E2ETestSystemExit(se.code)

    def cli_call(self, *given_args: str) -> str:
        return self.cli_call_helper("sys.stdout", *given_args)

    def assert_cli_output(
        self, args: t.Iterable[str], expected_output: t.Union[str, t.Dict[int, str]]
    ) -> None:
        output = self.cli_call(*args)
        if isinstance(expected_output, str):
            self.assertEqual(expected_output.strip(), output.strip())
            return
        lines = output.strip().split("\n")
        for line, expected_line_output in expected_output.items():
            if line < 0:
                self.assertGreaterEqual(line, -len(lines), expected_line_output)
            else:
                self.assertLess(line, len(lines), expected_line_output)
            self.assertEqual(lines[line], expected_line_output)

    def assert_cli_usage_error(
        self, args: t.Iterable[str], msg_regex: str = None
    ) -> None:
        with self.assertRaises((CommandError, E2ETestSystemExit)) as ex:
            self.cli_call(*args)
        exception = t.cast(t.Union[CommandError, E2ETestSystemExit], ex.exception)
        self.assertEqual(exception.returncode, 2)
        if msg_regex is not None:
            self.assertRegex(str(exception), msg_regex)

    def assert_cli_error_output(
        self, given_args: t.Iterable[str], expected_err: t.Union[str, t.Dict[int, str]]
    ) -> None:
        output = self.cli_call_helper("sys.stderr", *given_args)
        self.assertEqual(expected_err, output.strip())
