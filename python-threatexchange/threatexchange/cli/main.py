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
import logging
import inspect
import os
import sys
import typing as t
import pathlib
import shutil

from threatexchange import meta
from threatexchange.content_type.content_base import ContentType
from threatexchange.extensions.manifest import ThreatExchangeExtensionManifest
from threatexchange.exchanges.clients.fb_threatexchange import api as tx_api
from threatexchange.exchanges.clients.ncmec import hash_api as ncmec_api
from threatexchange.exchanges.impl.file_api import LocalFileSignalExchangeAPI
from threatexchange.exchanges.impl.static_sample import StaticSampleSignalExchangeAPI
from threatexchange.exchanges.impl.fb_threatexchange_api import (
    FBThreatExchangeSignalExchangeAPI,
)
from threatexchange.exchanges.impl.stop_ncii_api import StopNCIISignalExchangeAPI
from threatexchange.exchanges.impl.ncmec_api import NCMECSignalExchangeAPI

from threatexchange.content_type import photo, video, text, url
from threatexchange.exchanges.signal_exchange_api import SignalExchangeAPI
from threatexchange.signal_type import (
    pdq,
    md5,
    raw_text,
    url as url_signal,
    url_md5,
    trend_query,
)
from threatexchange.cli.cli_config import CLiConfig, CliState, StopNCIIKeys
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
    pdq.PdqSignal,
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
    subparsers = ap.add_subparsers(
        dest="toplevel_command_name", title="verbs", help="which action to do"
    )
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
    """
    Get the API key from a variety of fallback sources

    Examples might be environment, files, etc
    """

    environment_var = "TX_STOPNCII_KEYS"

    def get_from_environ() -> t.Optional[StopNCIIKeys]:
        val = os.environ.get(environment_var)
        if val is None:
            return None
        subscription_key, _, fetch_key = val.partition(",")
        return StopNCIIKeys(subscription_key, fetch_key)

    potential_sources = (
        (get_from_environ(), f"{environment_var} environment variable"),
        (
            config.stop_ncii_keys,
            "`config api stop_ncii --api-keys` command",
        ),
    )

    for val, source in potential_sources:
        if not val:
            continue
        val.subscription_key = val.subscription_key.strip()
        val.fetch_function_key = val.fetch_function_key.strip()

        if val.keys_are_valid:
            return val.subscription_key, val.fetch_function_key
        print(
            "Warning! Your current StopNCII.org keys "
            f"{val!r} (from {source}) are invalid.",
            file=sys.stderr,
        )
        # Don't throw because we don't want to block commands that fix this
        return None, None  # We probably don't expect to fall back here
    return None, None


def _get_ncmec_credentials(config: CLiConfig) -> t.Tuple[str, str]:
    """Get user+pass from NCMEC from the config"""
    environment_var = "TX_NCMEC_CREDENTIALS"
    not_found = "", ""

    def get_from_environ() -> t.Optional[t.Tuple[str, str]]:
        val = os.environ.get(environment_var)
        if val is None:
            return None
        user, _, password = val.partition(",")
        return user, password

    potential_sources = (
        (get_from_environ(), f"{environment_var} environment variable"),
        (
            config.ncmec_credentials,
            "`config api ncmec --user --pass` command",
        ),
    )

    for val, source in potential_sources:
        if not val:
            continue
        user, password = val

        if ncmec_api.is_valid_user_pass(user, password):
            return user, password
        print(
            "Warning! Your current NCMEC credentials "
            f"user={user!r} pass={password!r} (from {source}) are invalid.",
            file=sys.stderr,
        )
        # Don't throw because we don't want to block commands that fix this
        return not_found  # We probably don't expect to fall back here
    return not_found


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
        list(_DEFAULT_SIGNAL_TYPES) + extensions.signal_types,
    )
    base_apis: t.List[SignalExchangeAPI] = [
        StaticSampleSignalExchangeAPI(),
        LocalFileSignalExchangeAPI(),
        StopNCIISignalExchangeAPI(*_get_stopncii_tokens(config)),
        NCMECSignalExchangeAPI(*_get_ncmec_credentials(config)),
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
    if namespace.factory_reset:
        print("Resetting to factory defaults.", file=sys.stderr)
        shutil.rmtree(str(state_dir.expanduser().absolute()))
        return
    if not namespace.is_config:
        extensions.assert_no_errors()
    if not namespace.toplevel_command_name:
        ap.print_help()
        return
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
