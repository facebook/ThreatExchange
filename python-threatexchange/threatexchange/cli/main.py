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
import logging
import inspect
import os
import sys
import typing as t
import pathlib

from threatexchange import meta
from threatexchange.content_type.content_base import ContentType
from threatexchange.extensions.manifest import ThreatExchangeExtensionManifest
from threatexchange.fb_threatexchange import api as tx_api
from threatexchange.fetcher.apis.file_api import LocalFileSignalExchangeAPI
from threatexchange.fetcher.apis.static_sample import StaticSampleSignalExchangeAPI
from threatexchange.fetcher.apis.fb_threatexchange_api import (
    FBThreatExchangeSignalExchangeAPI,
)
from threatexchange.fetcher.apis.stop_ncii_api import StopNCIISignalExchangeAPI

from threatexchange.content_type import photo, video, text, url
from threatexchange.fetcher.fetch_api import SignalExchangeAPI
from threatexchange.signal_type import (
    pdq,
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
    ap.add_argument(
        "--app-token",
        "-a",
        metavar="TOKEN",
        help="the App token for ThreatExchange",
    )
    # is_config = Safe mode to try and let you fix bad settings from CLI
    ap.set_defaults(is_config=False)
    subparsers = ap.add_subparsers(title="verbs", help="which action to do")
    for command in get_subcommands():
        command.add_command_to_subparser(settings, subparsers)

    return ap


def execute_command(settings: CLISettings, namespace) -> None:
    assert hasattr(namespace, "command_cls")
    command_cls = namespace.command_cls
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


def _get_fb_tx_app_token(config: CLiConfig) -> t.Optional[str]:
    """
    Get the API key from a variety of fallback sources

    Examples might be environment, files, etc
    """

    file_loc = pathlib.Path("~/.txtoken").expanduser()
    environment_var = "TX_ACCESS_TOKEN"

    potential_sources = (
        (os.environ.get(environment_var), f"{environment_var} environment variable"),
        (
            config.fb_threatexchange_api_token,
            "`config api fb_threat_exchange --api-token` command",
        ),
        (file_loc.exists() and file_loc.read_text(), f"{file_loc} file"),
    )

    for val, source in potential_sources:
        if not val:
            continue
        val = val.strip()
        if tx_api.is_valid_app_token(val):
            return val
        print(
            (
                f"Warning! Your current app token {val!r} (from {source}) is invalid.\n"
                "Double check that it's an 'App Token' from "
                "https://developers.facebook.com/tools/accesstoken/",
            ),
            file=sys.stderr,
        )
        # Don't throw because we don't want to block commands that fix this
        return None  # We probably don't expect to fall back here
    return None


def _get_stopncii_tokens(
    config: CLiConfig,
) -> t.Tuple[t.Optional[str], t.Optional[str]]:
    """Get the API keys for StopNCII from the config"""
    return None, None  # TODO


class _ExtendedTypes(t.NamedTuple):
    content_types: t.List[t.Type[ContentType]]
    signal_types: t.List[t.Type[SignalType]]
    api_instances: t.List[SignalExchangeAPI]
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
            ret.api_instances.extend(api() for api in manifest.apis)
    return ret


def _get_settings(
    config: CLiConfig, dir: pathlib.Path
) -> t.Tuple[CLISettings, _ExtendedTypes]:
    """
    Configure the behavior and functionality.
    """

    extensions = _get_extended_functionality(config)

    signals = meta.SignalTypeMapping(
        [photo.PhotoContent, video.VideoContent, url.URLContent, text.TextContent]
        + extensions.content_types,
        [
            pdq.PdqSignal,
            md5.VideoMD5Signal,
            raw_text.RawTextSignal,
            url_signal.URLSignal,
            url_md5.UrlMD5Signal,
            trend_query.TrendQuerySignal,
        ]
        + extensions.signal_types,
    )
    base_apis: t.List[SignalExchangeAPI] = [
        StaticSampleSignalExchangeAPI(),
        LocalFileSignalExchangeAPI(),
        StopNCIISignalExchangeAPI(*_get_stopncii_tokens(config)),
        FBThreatExchangeSignalExchangeAPI(_get_fb_tx_app_token(config)),
    ]
    fetchers = meta.FetcherMapping(base_apis + extensions.api_instances)
    state = CliState(list(fetchers.fetchers_by_name.values()), dir=dir)

    return (
        CLISettings(meta.FunctionalityMapping(signals, fetchers, state), state),
        extensions,
    )


def _setup_logging():
    level = logging.DEBUG
    verbose = os.getenv("TX_VERBOSE", "0")
    if verbose == "0":
        level = logging.CRITICAL
    if verbose == "1":
        level = logging.INFO
    logging.basicConfig(
        format="%(asctime)s %(levelname).1s] %(message)s", level=level, force=True
    )


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
    if not namespace.is_config:
        extensions.assert_no_errors()
    execute_command(settings, namespace)


def main():
    """The main called by pip"""
    _setup_logging()
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
