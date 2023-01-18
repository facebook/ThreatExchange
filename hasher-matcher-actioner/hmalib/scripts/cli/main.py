#!/usr/bin/env python
# Copyright (c) Meta Platforms, Inc. and affiliates.

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

import hmalib.scripts.common.utils as utils

import hmalib.scripts.cli.command_base as base
import hmalib.scripts.cli.soak as soak
import hmalib.scripts.cli.storm as storm
import hmalib.scripts.cli.shell as shell
from hmalib.scripts.cli import run_api, run_lambda, print_tfvars_example, migrate

TERRAFORM_OUTPUTS_CACHE = "/tmp/hma-terraform-outputs.json"


def get_subcommands() -> t.List[t.Type[base.Command]]:
    return [
        soak.SoakCommand,
        storm.StormCommand,
        shell.ShellCommand,
        run_lambda.RunLambdaCommand,
        run_api.RunAPICommand,
        print_tfvars_example.PrintTFVarsExampleCommand,
        migrate.MigrateCommand,
    ]


def get_argparse() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--access-token",
        "-a",
        metavar="HMA_TOKEN",
        help="the acccess token for HMA API",
    )
    ap.add_argument(
        "--api-endpoint",
        "-e",
        metavar="HMA_API_URL",
        help="the url of the HMA API",
    )
    ap.add_argument(
        "--refresh-tf-outputs",
        "-r",
        help="Refresh terraform outputs",
        action="store_true",
    )

    subparsers = ap.add_subparsers(title="sub_commands", help="which action to do")
    for command in get_subcommands():
        command.add_command_to_subparser(subparsers)

    return ap


def get_terraform_outputs(refresh=False) -> t.Dict:
    if refresh and pathlib.Path(TERRAFORM_OUTPUTS_CACHE).exists():
        os.remove(TERRAFORM_OUTPUTS_CACHE)

    return utils.get_cached_terraform_outputs(TERRAFORM_OUTPUTS_CACHE)


def execute_command(namespace) -> None:
    if not hasattr(namespace, "command_cls"):
        get_argparse().print_help()
        return

    command_cls = namespace.command_cls
    try:
        command_argspec = inspect.getfullargspec(command_cls.__init__)
        arg_names = set(command_argspec[0])
        # Since we didn't import click, use hard-to-debug magic to init the command
        command = command_cls(
            **{k: v for k, v in namespace.__dict__.items() if k in arg_names}
        )

        if issubclass(command_cls, base.NeedsAPIAccess):
            # Init Values
            api = utils.HasherMatcherActionerAPI(
                get_api_url(
                    cli_option=namespace.api_endpoint,
                    refresh=namespace.refresh_tf_outputs,
                ),
                api_token=get_access_token(namespace.access_token),
            )

            command.execute(api)
        elif issubclass(command_cls, base.NeedsTerraformOutputs):
            tf_outputs = get_terraform_outputs(namespace.refresh_tf_outputs)
            command.execute(tf_outputs)
        else:
            # Command does not seem to require injection of any specific
            # arguments. Just execute it.
            command.execute()

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
    if cli_option:
        token = cli_option
    elif os.environ.get(environment_var):
        token = os.environ[environment_var]
    elif file_loc.exists() and file_loc.read_text():
        token = file_loc.read_text()
    else:
        raise base.CommandError(
            (
                "Can't find Access Token, pass it in using one of: \n"
                "  * a cli argument (-a)\n"
                f"  * in the environment as {environment_var}\n"
                f"  * in a file at {file_loc}\n"
            ),
            2,
        )
    token = token.strip()
    return token


def get_api_url(cli_option: str = None, refresh=False) -> str:
    """Get the API url cli args, environment_var, or tf outputs"""

    environment_var = "HMA_API_URL"
    url = ""
    if cli_option:
        url = cli_option
    elif os.environ.get(environment_var):
        url = os.environ[environment_var]
    else:
        print(
            "Trying to get API_URL from tf outputs.\n"
            "You can save time by passing it in using one of: \n"
            "  * a cli argument (-e)\n"
            f"  * in the environment as {environment_var}\n"
        )
        tf_outputs = get_terraform_outputs(refresh)
        url = tf_outputs["api_url"]
    return url


def main(args: t.Optional[t.Sequence[t.Text]] = None) -> None:
    ap = get_argparse()
    namespace = ap.parse_args(args)

    execute_command(namespace)


if __name__ == "__main__":
    main()
