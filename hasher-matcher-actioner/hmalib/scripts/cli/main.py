#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
A wrapper around hmacli operations.
"""

import argparse
import inspect
import os
import os.path
import pathlib
import re
import sys
import typing as t


import hmalib.scripts.cli.command_base as base
import hmalib.scripts.cli.soak as soak


def get_subcommands() -> t.List[t.Type[base.Command]]:
    return [soak.SoakCommand]


def get_argparse() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--access-token",
        "-a",
        metavar="TOKEN",
        help="the acccess token for HMA API",
    )
    ap.add_argument(
        "--api-endpoint",
        "-E",
        help=argparse.SUPPRESS,
    )
    subparsers = ap.add_subparsers(title="sub_commands", help="which action to do")
    for command in get_subcommands():
        command.add_command_to_subparser(subparsers)

    return ap


def execute_command(namespace) -> None:
    if not hasattr(namespace, "command_cls"):
        get_argparse().print_help()
        return
    command_cls = namespace.command_cls
    try:
        # Init Values
        api = "Hi"

        command_argspec = inspect.getfullargspec(command_cls.__init__)
        arg_names = set(command_argspec[0])
        # Since we didn't import click, use hard-to-debug magic to init the command
        command = command_cls(
            **{k: v for k, v in namespace.__dict__.items() if k in arg_names}
        )
        command.execute(api)
    except base.CommandError as ce:
        print(ce, file=sys.stderr)
        sys.exit(ce.returncode)
    except KeyboardInterrupt:
        # No stack for CTRL+C
        sys.exit(130)


def get_access_token(cli_option: str = None) -> str:
    """Get the API token from a variety of fallback sources"""

    file_loc = pathlib.Path("~/.hmatoken").expanduser()
    environment_var = "HMA_TOKEN"
    token = ""
    source = ""
    if cli_option:
        source = "cli argument"
        token = cli_option
    elif os.environ.get(environment_var):
        source = f"{environment_var} environment variable"
        token = os.environ[environment_var]
    elif file_loc.exists() and file_loc.read_text():
        source = str(file_loc)
        token = file_loc.read_text()
    else:
        raise base.CommandError(
            (
                "Can't find Access Token, pass it in using one of: \n"
                "  * a cli argument\n"
                f"  * in the environment as {environment_var}\n"
                f"  * in a file at {file_loc}\n"
            ),
            2,
        )
    token = token.strip()
    return token


def main(args: t.Optional[t.Sequence[t.Text]] = None) -> None:
    ap = get_argparse()
    namespace = ap.parse_args(args)
    execute_command(namespace)


if __name__ == "__main__":
    main()
