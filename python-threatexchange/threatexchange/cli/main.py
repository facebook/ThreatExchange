# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrapper for the `threatexchange` library, can serve as a simple e2e solution.

The flow the CLI is generally:
  1. Configure collaborations and APIs with (or skip to use fake sample data)
     $ threatexchange config collab edit
     $ threatexchange config api  # to set up credentials if needed
  2. Fetch data and build match indices
     $ threatexchange fetch
  3. Match data
     $ threatexchange match photo my_photo.jpg
  4. Contribute labels to external APIs
     $ threatexchange label photo my_photo.jpg dog 
     $ threatexchange label photo my_photo.jpg --false-positive

Additionally, there are a number of utility commands:
  * threatexchange dataset
  * threatexchange hash

See the --help of subcommands for more information.

State is persisted between runs, entirely in the ~/.threatexchange directory
"""

import argparse
from contextlib import contextmanager
import logging
import inspect
import os
import sys
import typing as t
import pathlib
import shutil
import warnings

# Import pdq first with its hash order warning squelched, it's before our time
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from threatexchange.signal_type.pdq import signal

from threatexchange.cli.exceptions import CommandError
from threatexchange import interface_validation
from threatexchange.content_type.content_base import ContentType
from threatexchange.extensions.manifest import ThreatExchangeExtensionManifest
from threatexchange.exchanges.impl.file_api import LocalFileSignalExchangeAPI
from threatexchange.exchanges.impl.static_sample import StaticSampleSignalExchangeAPI
from threatexchange.exchanges.impl.fb_threatexchange_api import (
    FBThreatExchangeCredentials,
    FBThreatExchangeSignalExchangeAPI,
)
from threatexchange.exchanges.impl.stop_ncii_api import (
    StopNCIICredentials,
    StopNCIISignalExchangeAPI,
)
from threatexchange.exchanges.impl.ncmec_api import (
    NCMECCredentials,
    NCMECSignalExchangeAPI,
)

from threatexchange.content_type import photo, video, text, url
from threatexchange.exchanges.signal_exchange_api import SignalExchangeAPI
from threatexchange.exchanges.auth import (
    SignalExchangeAPIInvalidAuthException,
    SignalExchangeAPIMissingAuthException,
)
from threatexchange.signal_type import (
    md5,
    raw_text,
    url as url_signal,
    url_md5,
    trend_query,
)
from threatexchange.cli.cli_config import CLiConfig, CliState
from threatexchange.cli.cli_config import CLISettings
from threatexchange.cli import (
    command_base as base,
    fetch_cmd,
    label_cmd,
    dataset_cmd,
    hash_cmd,
    match_cmd,
    config_cmd,
)
from threatexchange.signal_type.signal_base import SignalType

_DEFAULT_SIGNAL_TYPES: t.Sequence[t.Type[SignalType]] = [
    signal.PdqSignal,
    md5.VideoMD5Signal,
    raw_text.RawTextSignal,
    url_signal.URLSignal,
    url_md5.UrlMD5Signal,
    trend_query.TrendQuerySignal,
]


def get_subcommands() -> t.List[t.Type[base.Command]]:
    return [
        config_cmd.ConfigCommand,
        fetch_cmd.FetchCommand,
        match_cmd.MatchCommand,
        label_cmd.LabelCommand,
        dataset_cmd.DatasetCommand,
        hash_cmd.HashCommand,
    ]


def get_argparse(settings: CLISettings) -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    # is_config = Safe mode to try and let you fix bad settings from CLI
    ap.set_defaults(is_config=False)
    ap.add_argument(
        "--factory-reset",
        action="store_true",
        help="Remove all state, bringing you back to a fresh install",
    )
    ap.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="display logging output (repeat for more)",
    )
    subparsers = ap.add_subparsers(
        dest="toplevel_command_name", title="verbs", help="which action to do"
    )
    for command in get_subcommands():
        command.add_command_to_subparser(settings, subparsers)

    return ap


def execute_command(settings: CLISettings, namespace) -> None:
    assert hasattr(namespace, "command_cls")
    command_cls: t.Type[base.Command] = namespace.command_cls
    logging.debug("Setup complete, handing off to %s", command_cls.__name__)
    # Init everything
    command_argspec = inspect.getfullargspec(command_cls.__init__)
    arg_names = set(command_argspec[0])
    # Since we didn't import click, use hard-to-debug magic to init the command
    command_args = {k: v for k, v in namespace.__dict__.items() if k in arg_names}
    if "full_argparse_namespace" in arg_names:
        command_args["full_argparse_namespace"] = namespace

    command = command_cls(**command_args)
    command.execute(settings)


@contextmanager
def _handle_api_creds(config: CLiConfig) -> t.Iterator[None]:
    te_creds = None
    ncmec_creds = None
    stop_ncii_creds = config.stop_ncii_keys

    def cfg_cmd(src_api: t.Type[SignalExchangeAPI], flags: str) -> str:
        return f"threatexchange config api {src_api.get_name()} {flags}"

    if config.fb_threatexchange_api_token:
        te_creds = FBThreatExchangeCredentials(config.fb_threatexchange_api_token)
    if config.ncmec_credentials:
        ncmec_creds = NCMECCredentials(*config.ncmec_credentials)

    with FBThreatExchangeCredentials.set_default(
        te_creds, cfg_cmd(FBThreatExchangeSignalExchangeAPI, "--api-token")
    ), NCMECCredentials.set_default(
        ncmec_creds, cfg_cmd(NCMECSignalExchangeAPI, "--user --pass")
    ), StopNCIICredentials.set_default(
        stop_ncii_creds, cfg_cmd(StopNCIISignalExchangeAPI, "<TBD>")  # TODO
    ):
        try:
            yield
        except SignalExchangeAPIInvalidAuthException as ia:
            logging.exception("Original invalid auth error")
            raise CommandError.user(
                f"Invalid auth for {ia.src_api.get_name()}: {ia.message}"
            ) from ia
        except SignalExchangeAPIMissingAuthException as ma:
            logging.exception("Original missing auth error")
            raise CommandError.user(ma.pretty_str()) from ma


class _ExtendedTypes(t.NamedTuple):
    content_types: t.List[t.Type[ContentType]]
    signal_types: t.List[t.Type[SignalType]]
    api_types: t.List[t.Type[SignalExchangeAPI]]
    load_failures: t.List[str]

    def assert_no_errors(self) -> None:
        if not self.load_failures:
            return
        err_list = "\n  ".join(self.load_failures)
        raise base.CommandError.user(
            "Some extensions are no longer loadable! You might need to "
            "re-install, or else remove them with the "
            "`threatexchange config extensions remove` command:\n  "
            f"{err_list}"
        )


def _get_extended_functionality(config: CLiConfig) -> _ExtendedTypes:
    ret = _ExtendedTypes([], [], [], [])
    for extension in config.extensions:
        logging.debug("Loading extension %s", extension)
        try:
            manifest = ThreatExchangeExtensionManifest.load_from_module_name(extension)
        except (ValueError, ImportError):
            ret.load_failures.append(extension)
        else:
            ret.signal_types.extend(manifest.signal_types)
            ret.content_types.extend(manifest.content_types)
            ret.api_types.extend(manifest.apis)
    return ret


def _get_settings(
    config: CLiConfig, dir: pathlib.Path
) -> t.Tuple[CLISettings, _ExtendedTypes]:
    """
    Configure the behavior and functionality.
    """

    extensions = _get_extended_functionality(config)

    signals = interface_validation.SignalTypeMapping(
        [photo.PhotoContent, video.VideoContent, url.URLContent, text.TextContent]
        + extensions.content_types,
        list(_DEFAULT_SIGNAL_TYPES) + extensions.signal_types,
    )
    base_apis: t.List[t.Type[SignalExchangeAPI]] = [
        StaticSampleSignalExchangeAPI,
        LocalFileSignalExchangeAPI,
        StopNCIISignalExchangeAPI,
        NCMECSignalExchangeAPI,
        FBThreatExchangeSignalExchangeAPI,
    ]
    apis = interface_validation.SignalExchangeAPIMapping(
        base_apis + extensions.api_types
    )
    state = CliState(list(apis.api_by_name.values()), dir=dir)

    return (
        CLISettings(
            interface_validation.FunctionalityMapping(signals, apis, state), state
        ),
        extensions,
    )


def _setup_logging(level_str: str, *, initial: bool = False) -> None:
    level = logging.DEBUG
    if level_str == "0":
        level = logging.CRITICAL
    elif level_str == "1":
        level = logging.INFO
    if initial:
        logging.basicConfig(
            format="%(asctime)s %(levelname).1s] %(message)s", level=level, force=True
        )
    else:
        logging.getLogger().setLevel(level)


def inner_main(
    args: t.Optional[t.Sequence[t.Text]] = None,
    state_dir: pathlib.Path = pathlib.Path("~/.threatexchange"),
) -> None:
    """The main called by tests"""
    config = CliState(
        [], state_dir
    ).get_persistent_config()  # TODO fix the circular dependency
    settings, extensions = _get_settings(config, state_dir)
    ap = get_argparse(settings)
    namespace = ap.parse_args(args)
    if namespace.verbose:
        _setup_logging(str(namespace.verbose))
    if namespace.factory_reset:
        print("Resetting to factory defaults.", file=sys.stderr)
        shutil.rmtree(str(state_dir.expanduser().absolute()))
        return
    if not namespace.is_config:
        extensions.assert_no_errors()
    if not namespace.toplevel_command_name:
        ap.print_help()
        return
    with _handle_api_creds(settings.get_persistent_config()):
        execute_command(settings, namespace)


def main():
    """The main called by pip"""
    _setup_logging(os.getenv("TX_VERBOSE", "0"), initial=True)
    try:
        inner_main()
    except base.CommandError as ce:
        print(ce, file=sys.stderr)
        sys.exit(ce.returncode)
    except KeyboardInterrupt:
        # No stack for CTRL+C
        sys.exit(130)


# Surprise! This line is not actually called when installed as a script by pip
if __name__ == "__main__":
    main()  # Don't add anything else here
