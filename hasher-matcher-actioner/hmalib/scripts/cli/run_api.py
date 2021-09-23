# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

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
        pass

    @classmethod
    def get_name(cls) -> str:
        return "run-api"

    @classmethod
    def get_help(cls) -> str:
        return "Runs the bottle application locally. Fetches environment variables from the provisioned lambda."

    def execute(self, tf_outputs: t.Dict) -> None:
        full_lambda_name = f"{tf_outputs['prefix']}_api_root"
        fn_configuration = get_lambda_client().get_function_configuration(
            FunctionName=full_lambda_name
        )

        fn_env_vars = fn_configuration["Environment"]["Variables"]
        for k in fn_env_vars:
            os.environ[k] = fn_env_vars[k]

        from hmalib.lambdas.api.api_root import app

        app.run()
