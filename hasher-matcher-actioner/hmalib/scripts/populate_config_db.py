#! /usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

# type: ignore

"""
Write simple configs to the HMA config database
"""

import argparse
from dataclasses import fields
import getpass
import json
import tempfile
import subprocess
import typing as t
import re

from hmalib.lambdas.fetcher import ThreatExchangeConfig
from hmalib.common import config as hmaconfig
from hmalib.common.actioner_models import WebhookPostActionPerformer

SUPPORTED_CONFIGS = [
    ThreatExchangeConfig,
]


def better_bool_type(s: str):
    s = s.strip().lower()
    if s in ("true", "1"):
        return True
    if s in ("false", "0"):
        return False

    raise argparse.ArgumentTypeError("for bools use 'true' or 'false'")


def get_configs(args):
    config_cls = {config_cls.__name__: config_cls for config_cls in SUPPORTED_CONFIGS}[
        args.config_type
    ]
    if args.name:
        print(config_cls.getx(args.name))
        return
    for config in config_cls.get_all():
        print(config)


def edit_config(args):
    """Update a config of the chosen type"""
    kwargs = {}
    for field in fields(args.config_cls):
        kwargs[field.name] = getattr(args, field.name)
    config = args.config_cls(**kwargs)
    hmaconfig.update_config(config)
    print(config)


def load_defaults(_args):
    """
    Load a hardcoded set of defaults which are useful in testing
    """

    # Could also put the default on the class, but seems too fancy
    configs = [
        ThreatExchangeConfig(
            "303636684709969",
            fetcher_active=True,
            privacy_group_name="Test Config 1",
        ),
        ThreatExchangeConfig(
            "258601789084078",
            fetcher_active=True,
            privacy_group_name="Test Config 2",
        ),
        WebhookPostActionPerformer(
            name="EnqueForReviewAction",
            url="https://webhook.site/ff7ebc37-514a-439e-9a03-46f86989e195",
        ),
    ]
    for config in configs:
        # Someday maybe can do filtering or something, I dunno
        hmaconfig.update_config(config)
        print(config)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--table",
        default=f"{getpass.getuser()}-HMAConfig",
        help="The name of the config dynamodb table",
    )
    subparsers = parser.add_subparsers()
    # Update
    update = subparsers.add_parser("update", help="Add or edit a config")
    update_subparsers = update.add_subparsers()
    for config_cls in SUPPORTED_CONFIGS:
        sub = update_subparsers.add_parser(
            config_cls.__name__, help="Update a config of this type"
        )
        sub.set_defaults(config_cls=config_cls, fn=edit_config)
        for field in fields(config_cls):
            origin = t.get_origin(field.type)
            parse_type = str
            addtl_kwargs = {}
            if field.type in (str, float, int):
                parse_type = field.type
            elif field.type is bool:
                parse_type = better_bool_type
            elif field.type in (t.Set[str], t.List[str]):
                parse_type = lambda x: set(x.split(","))
            else:
                raise Exception(f"Unsupported type in config: {field.type}")
            arg = field.name
            if arg != "name":
                arg = f"--{arg}"
                addtl_kwargs["required"] = True
            sub.add_argument(
                arg,
                type=parse_type,
                metavar=re.sub(
                    r"^typing.",
                    "",
                    re.sub(r"<class '([^']+)'>", r"\1", str(field.type)),
                ),
                help=f"{field.name}",
                **addtl_kwargs,
            )
    # load_examples
    ex_subparser = subparsers.add_parser(
        "load_example_configs", help="Populate db with a default set of configs"
    )
    ex_subparser.set_defaults(fn=load_defaults)
    # get
    get_config_parser = subparsers.add_parser("get", help="get configs")
    get_config_parser.add_argument(
        "config_type",
        choices=[config_cls.__name__ for config_cls in SUPPORTED_CONFIGS],
        help="which config type to get",
    )
    get_config_parser.add_argument("--name", help="the name of the config")
    get_config_parser.set_defaults(fn=get_configs)

    args = parser.parse_args()
    hmaconfig.HMAConfig.initialize(args.table)
    args.fn(args)
