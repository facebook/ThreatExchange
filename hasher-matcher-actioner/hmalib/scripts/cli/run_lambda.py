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


class RunLambdaCommand(base.Command, base.NeedsTerraformOutputs):
    @classmethod
    def init_argparse(cls, ap: argparse.ArgumentParser) -> None:
        ap.add_argument(
            "--lambda-name", help="Lambda name without the prefix. eg. hasher, api_root"
        )

    @classmethod
    def get_name(cls) -> str:
        return "run-lambda"

    @classmethod
    def get_help(cls) -> str:
        return "Runs a single lambda. You can use this to run or debug lambdas locally."

    def __init__(self, lambda_name: str) -> None:
        self.lambda_name = lambda_name

    def execute(self, tf_outputs: t.Dict) -> None:
        full_lambda_name = f"{tf_outputs['prefix']}_{self.lambda_name}"
        fn_configuration = get_lambda_client().get_function_configuration(
            FunctionName=full_lambda_name
        )

        fn_env_vars = fn_configuration["Environment"]["Variables"]
        fn_method = fn_configuration["ImageConfigResponse"]["ImageConfig"]["Command"][0]

        for k in fn_env_vars:
            os.environ[k] = fn_env_vars[k]

        module_name, fn_name = fn_method.rsplit(".", 1)
        module = importlib.import_module(module_name)
        fn = getattr(module, fn_name)

        try:
            from lambda_local import get_event  # type: ignore

            fn(get_event(self.lambda_name), None)
        except ModuleNotFoundError:
            print(
                "Please define variable `event` in hasher-matcher-actioner/lambda_local.py"
            )
            sys.exit(1)
