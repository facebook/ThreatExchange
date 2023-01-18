# Copyright (c) Meta Platforms, Inc. and affiliates.

import typing as t
import argparse
import importlib
import sys

from hmalib.common.config import HMAConfig
import hmalib.scripts.cli.command_base as base
from hmalib.scripts.migrations.migrations_base import MigrationBase


class MigrateCommand(base.Command):
    """
    Executes a migration identified by a name.

    eg. "$ python -m hmalib.scripts.cli.main migrate
    2022_04_02_default_content_signal_type_configs"

    Will execute the do_migrate function in the
    "hmalib.scripts.migrations.2022_04_02_default_content_signal_type_configs"
    module.

    Right now, there is no state management done within the command. Doing a
    migration twice will cause it to happen twice. State-management is left to
    terraform. See terraform/migrations/main.tf.
    """

    @classmethod
    def init_argparse(cls, ap: argparse.ArgumentParser) -> None:
        ap.add_argument(
            "migration",
            help="Which migration to run? eg. 2022_04_02_default_content_signal_type_configs",
        )

        ap.add_argument("--config-table", help="Name of the HMA Config table.")

    @classmethod
    def get_name(cls) -> str:
        return "migrate"

    @classmethod
    def get_help(cls) -> str:
        return "Force-runs a migration identified by argument. eg. `$ migrate <foo>` will run the do_migrate method in hmalib.scripts.migrations.<foo>"

    def __init__(self, migration: str, config_table: str):
        self.migration = migration
        HMAConfig.initialize(config_table)

    def execute(self) -> None:
        module_name = f"hmalib.scripts.migrations.{self.migration}"
        try:
            module = importlib.import_module(module_name)

            if hasattr(module, "_Migration"):
                _migration_class: t.Type[
                    MigrationBase
                ] = module._Migration  # type:ignore
                _migration_instance = _migration_class()  # Expect no-args constructor
                _migration_instance.do_migrate()
            else:
                print(
                    f"ERROR: Class _Migration does not exist on module {module_name}. Can't migrate."
                )

        except ModuleNotFoundError:
            print(
                f"ERROR: Could not find migration {self.migration}. Does the module {module_name} exist?"
            )
            sys.exit(1)
