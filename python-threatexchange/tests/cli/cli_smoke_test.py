# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import sys
import pytest

from threatexchange.cli import main


def test_all_helps():
    """
    Just executes all the commands to make sure they don't throw on help.

    View the pretty output with py.test -s
    """

    def help(command=None):
        args = [command.get_name()] if command else []
        args.append("--help")

        with pytest.raises(SystemExit) as exc:
            print("\n$ threatexchange", " ".join(args), file=sys.stderr)
            main.main(args)
        assert exc.value.code == 0

    help()  # root help
    for command in main.get_subcommands():
        help(command)
