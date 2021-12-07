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
import re
import sys
import typing as t

from .. import descriptor
from ..api import ThreatExchangeAPI
from ..collab_config import CollaborationConfig
from ..dataset import Dataset
from . import (
    command_base as base,
    fetch,
    tag_fetch,
    label,
    match,
    dataset_cmd,
    hash_cmd,
)


def get_subcommands() -> t.List[t.Type[base.Command]]:
    return [
        fetch.FetchCommand,
        match.MatchCommand,
        label.LabelCommand,
        dataset_cmd.DatasetCommand,
        hash_cmd.HashCommand,
        tag_fetch.TagFetchCommand,
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
    ap.add_argument(
        "--fb-threatexchange-endpoint",
        "-E",
        # For facebook developers testing new APIs, allow pointing
        # to internal endpoints
        help=argparse.SUPPRESS,
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
        # Init API
        api = ThreatExchangeAPI(
            get_app_token(namespace.app_token),
            endpoint_override=namespace.fb_threatexchange_endpoint,
        )
        # Init state library (needs to be refactored)
        descriptor.ThreatDescriptor.MY_APP_ID = api.api_token.partition("|")[0]
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
        command.execute(api, dataset)
    except base.CommandError as ce:
        print(ce, file=sys.stderr)
        sys.exit(ce.returncode)
    except KeyboardInterrupt:
        # No stack for CTRL+C
        sys.exit(130)


def get_app_token(cli_option: str = None) -> str:
    """Get the API key from a variety of fallback sources"""

    file_loc = pathlib.Path("~/.txtoken").expanduser()
    environment_var = "TX_ACCESS_TOKEN"
    token = ""
    source: t.Union[pathlib.Path, str] = ""
    if cli_option:
        source = "cli argument"
        token = cli_option
    elif os.environ.get(environment_var):
        source = f"{environment_var} environment variable"
        token = os.environ[environment_var]
    elif file_loc.exists() and file_loc.read_text():
        source = file_loc
        token = file_loc.read_text()
    else:
        raise base.CommandError(
            (
                "Can't find App Token, pass it in using one of: \n"
                "  * a cli argument\n"
                f"  * in the environment as {environment_var}\n"
                f"  * in a file at {file_loc}\n"
                "https://developers.facebook.com/tools/accesstoken/"
            ),
            2,
        )
    token = token.strip()
    if not is_valid_app_token(token):
        raise base.CommandError(
            f"Your current app token (from {source}) is invalid.\n"
            "Double check that it's an 'App Token' from "
            "https://developers.facebook.com/tools/accesstoken/",
            2,
        )
    return token


def is_valid_app_token(token: str) -> bool:
    """Returns true if the string looks like a valid token"""
    return bool(re.match("[0-9]{8,}(?:%7C|\\|)[a-zA-Z0-9_\\-]{20,}", token))


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


def main(args: t.Optional[t.Sequence[t.Text]] = None) -> None:
    ap = get_argparse()
    namespace = ap.parse_args(args)
    execute_command(namespace)


if __name__ == "__main__":
    main()
