# Copyright (c) Meta Platforms, Inc. and affiliates.

import typing as t
from functools import lru_cache
import sys
import argparse
import importlib
import boto3
import os
import logging.config

LOGGING = {
    "version": 1,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        }
    },
    "root": {"level": "INFO", "handlers": ["console"]},
}

logging.config.dictConfig(LOGGING)

import hmalib.scripts.cli.command_base as base


@lru_cache(maxsize=None)
def get_lambda_client():
    return boto3.client("lambda")


class RunAPICommand(base.Command, base.NeedsTerraformOutputs):
    @classmethod
    def init_argparse(cls, ap: argparse.ArgumentParser) -> None:
        ap.add_argument(
            "--print-endpoints",
            "-p",
            help=f"instead of running. List all API endpoints and exit.",
            action="store_true",
        )

    @classmethod
    def get_name(cls) -> str:
        return "run-api"

    @classmethod
    def get_help(cls) -> str:
        return "Runs the bottle application locally. Fetches environment variables from the provisioned lambda."

    def __init__(self, print_endpoints: bool = False) -> None:
        self.print_endpoints = print_endpoints

    def execute(self, tf_outputs: t.Dict) -> None:
        full_lambda_name = f"{tf_outputs['prefix']}_api_root"
        fn_configuration = get_lambda_client().get_function_configuration(
            FunctionName=full_lambda_name
        )

        fn_env_vars = fn_configuration["Environment"]["Variables"]
        for k in fn_env_vars:
            os.environ[k] = fn_env_vars[k]

        # Inline imports because environment variables need to be set BEFORE we
        # do the import. api_root does os.environ lookups at module import.
        from hmalib.lambdas.api.api_root import bottle_init_once

        app = bottle_init_once()[0]

        if self.print_endpoints:
            print("\nPrinting all endpoints instead of running API:\n")
            self._print_endpoints(app)
        else:
            app.run()

    @classmethod
    def _get_endpoints(cls, app):
        for route in app.routes:
            if "mountpoint" in route.config:
                prefix = route.config["mountpoint.prefix"]
                subpath = route.config["mountpoint.target"]

                for prefixes, route in cls._get_endpoints(subpath):
                    yield [prefix] + prefixes, route
            else:
                yield [], route

    @classmethod
    def _print_endpoints(cls, app, with_doc=True):
        for prefixes, route in cls._get_endpoints(app):
            path = (
                "/" + "/".join(p.strip("/") for p in prefixes if p.strip("/"))
                if prefixes
                else ""
            )
            print(route.method, f"{path}{route.rule}", route.callback.__qualname__)
            if with_doc:
                print(route.callback.__doc__)
