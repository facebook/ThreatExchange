##!/usr/bin/env python

"""
A wrapper around multi-stage ThreatExchange operations.

Includes simple matching and writing back. Useful for quickly validating new
sources of ThreatExchange data. A possible template for a native
implementation in your own architecture.

This helper heavily relies on a config file to provide consistent behavior
between stages, and a state file to store hashes.
"""

import argparse
import os
import os.path
import pathlib
import sys
import typing as t

import TE

from .collab_config import CollaborationConfig
from .dataset import Dataset
from .commands import base, label, match, fetch


def get_subcommands() -> t.List[t.Type[base.Command]]:
    return [label.LabelCommand, match.MatchCommand, fetch.FetchCommand]


def get_argparse() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--config",
        "-c",
        type=argparse.FileType,
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
    command_cls = namespace.command_cls
    try:
        # Init TE lib
        init_app_token(namespace.app_token)
        # Init collab config
        cfg = init_config_file(namespace.config)
        # "Init" dataset
        dataset = Dataset(cfg, namespace.state_dir)
        command = command_cls.init_from_namespace(namespace)
        command.execute(dataset)
    except base.CommandError as ce:
        print(ce, file=sys.stderr)
        sys.exit(ce.returncode)


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
        raise base.CommandError(
            (
                "Can't find collaboration config - pass as an argument"
                f", or in a file named {' or '.join(path_order)}"
            ),
            2,
        )
    with path.open() as f:
        return CollaborationConfig.load(f)



def _verify_directory(raw: str) -> pathlib.Path:
    ret = pathlib.Path(raw)
    if ret.exists() and not ret.is_dir():
        raise argparse.ArgumentTypeError(f"{ret} is a file, not a directory")
    return ret


if __name__ == "__main__":
    ap = get_argparse()
    namespace = ap.parse_args()
    execute_command(namespace)
