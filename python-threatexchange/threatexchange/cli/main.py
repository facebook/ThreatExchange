#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
A wrapper around multi-stage ThreatExchange operations.

Includes simple matching and writing back. Useful for quickly validating new
sources of ThreatExchange data. A possible template for a native
implementation in your own architecture.

This helper heavily relies on a config file to provide consistent behavior
between stages, and a state file to store hashes.
"""

import argparse
import inspect
import os
import os.path
import pathlib
import sys
import typing as t

from .. import TE
from . import command_base as base, fetch, experimental_fetch, label, match
from ..collab_config import CollaborationConfig
from ..dataset import Dataset


def get_subcommands() -> t.List[t.Type[base.Command]]:
    return [
        fetch.FetchCommand,
        experimental_fetch.ExperimentalFetchCommand,
        match.MatchCommand,
        label.LabelCommand,
    ]


def get_argparse() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--config",
        "-c",
        type=argparse.FileType("r"),
        help="a ThreatExchange collaboration config",
    )
    ap.add_argument(
        "--app-token",
        "-a",
        type=CollaborationConfig.load,
        metavar="TOKEN",
        help="the App token for ThreatExchange",
    )
    ap.add_argument(
        "--state-dir",
        "-s",
        type=_verify_directory,
        metavar="DIR",
        help="the directory with the config state",
    )
    subparsers = ap.add_subparsers(title="verbs", help="which action to do")
    for command in get_subcommands():
        command.add_command_to_subparser(subparsers)

    return ap


def execute_command(namespace) -> None:
    if not hasattr(namespace, "command_cls"):
        get_argparse().print_help()
        return
    command_cls = namespace.command_cls
    try:
        # Init TE lib
        init_app_token(namespace.app_token)
        # Init collab config
        cfg = init_config_file(namespace.config)
        # "Init" dataset
        dataset = Dataset(cfg, namespace.state_dir)
        command_argspec = inspect.getfullargspec(command_cls.__init__)
        arg_names = set(command_argspec[0])
        # Since we didn't import click, use hard-to-debug magic to init the command
        command = command_cls(
            **{k: v for k, v in namespace.__dict__.items() if k in arg_names}
        )
        command.execute(dataset)
    except base.CommandError as ce:
        print(ce, file=sys.stderr)
        sys.exit(ce.returncode)
    except KeyboardInterrupt:
        # No stack for CTRL+C
        sys.exit(130)


def init_app_token(cli_option: str = None) -> None:
    """Initialize the API key from a variety of fallback sources"""

    file_loc = pathlib.Path("~/.txtoken").expanduser()
    environment_var = "TX_ACCESS_TOKEN"
    if cli_option:
        TE.Net.APP_TOKEN = cli_option
    elif os.environ.get(environment_var):
        TE.Net.APP_TOKEN = os.environ[environment_var]
    elif file_loc.exists() and file_loc.read_text():
        TE.Net.APP_TOKEN = file_loc.read_text()
    else:
        raise base.CommandError(
            (
                "Can't find API key - pass as an argument, in the environment as "
                f"{environment_var} or put it in {file_loc}"
            ),
            2,
        )


def init_config_file(cli_provided: t.IO = None) -> CollaborationConfig:
    """Initialize the collaboration file from a variety of sources"""
    if cli_provided is not None:
        return CollaborationConfig.load(cli_provided)
    path_order = ("te.cfg", "~/te.cfg")
    for loc in path_order:
        path = pathlib.Path(loc).expanduser()
        if path.exists():
            break
    else:
        print(
            (
                "Looks like you haven't set up a collaboration config, "
                "so using the sample one against public data"
            ),
            file=sys.stderr,
        )
        return CollaborationConfig.get_example_config()
    with path.open() as f:
        return CollaborationConfig.load(f)


def _verify_directory(raw: str) -> pathlib.Path:
    ret = pathlib.Path(raw)
    if ret.exists() and not ret.is_dir():
        raise argparse.ArgumentTypeError(f"{ret} is a file, not a directory")
    return ret


def main() -> None:
    ap = get_argparse()
    namespace = ap.parse_args()
    execute_command(namespace)


if __name__ == "__main__":
    main()
