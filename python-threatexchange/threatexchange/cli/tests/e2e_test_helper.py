# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved


import pathlib
import shutil
import tempfile
import unittest

from threatexchange.cli import main
from threatexchange.cli.exceptions import CommandError


class E2ETestSystemExit(Exception):
    def __init__(self, code: int) -> None:
        self.returncode = code


class ThreatExchangeCLIE2eTest(unittest.TestCase):

    _state_dir: pathlib.Path

    def setUp(self) -> None:
        super().setUp()

        self._state_dir = pathlib.Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        super().tearDown()

        if self._state_dir.is_dir():
            shutil.rmtree(str(self._state_dir))

    def cli_call(self, *args: str) -> None:
        try:
            main(args, state_dir = self._state_dir)
        except SystemExit as se:
            raise E2ETestSystemExit(se.code)

    def cli_call_assert_usage_error(self, *args: str, msg_regex: str = None) -> None:
        with self.assertRaises((CommandError, E2ETestSystemExit)) as ex:
            self.cli_call(args)
        self.assertEqual(ex.exception.returncode, 2)
        if msg_regex is not None:
            self.assertIsInstance(ex.exception, CommandError)
            self.assertRegex(ex.exception.args[0], msg_regex)
