# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import pytest
import sys
import typing as t

from _pytest.config import Config

from threatexchange.cli import main
from threatexchange.cli.command_base import Command, CommandWithSubcommands
from threatexchange.cli.tests.e2e_test_helper import ThreatExchangeCLIE2eHelper, te_cli

_PRINT_TO_STDERR: bool = False


def test_all_helps(te_cli: ThreatExchangeCLIE2eHelper, pytestconfig: Config):
    """
    Just executes all the commands to make sure they don't throw on help.

    View the pretty output with py.test -sv
    """
    global _PRINT_TO_STDERR
    _PRINT_TO_STDERR = pytestconfig.getoption("verbose") > 0
    te_cli.cli_call()  # root help
    _run_help(te_cli)  # root help
    for command in main.get_subcommands():
        _recurse(te_cli, command)


def _run_help(te_cli: ThreatExchangeCLIE2eHelper, *args: str) -> None:
    out = te_cli.cli_call(*args, "--help")
    if _PRINT_TO_STDERR:
        print(out, file=sys.stderr)


def _recurse(
    te_cli: ThreatExchangeCLIE2eHelper, command: t.Type[Command], *parents: str
) -> None:
    name = command.get_name()
    _run_help(te_cli, *parents, name)
    if issubclass(command, CommandWithSubcommands):
        for subcommand in command._SUBCOMMANDS:
            _recurse(te_cli, subcommand, *parents, name)
