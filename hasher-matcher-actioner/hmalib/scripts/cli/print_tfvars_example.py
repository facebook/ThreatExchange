# Copyright (c) Meta Platforms, Inc. and affiliates.

import argparse
import warnings

import hmalib.scripts.cli.command_base as base

MAX_LINE_LENGTH = 80
MAIN_VARIABLES_FILE = "terraform/variables.tf"


class PrintTFVarsExampleCommand(base.Command):
    """
    Takes the root input variables declaration file in
    hasher-matcher-actioner/teraform directory and writes an example file
    complete with description and defaults.

    Input file is hardcoded. Output is to stdin.
    """

    @classmethod
    def init_argparse(cls, ap: argparse.ArgumentParser) -> None:
        return super().init_argparse(ap)

    @classmethod
    def get_name(cls) -> str:
        return "print-tfvars-example"

    @classmethod
    def get_help(cls) -> str:
        return (
            "Converts terraform input variable declaration files into an config file."
        )

    @staticmethod
    def _print_single_variable(name: str, description: str, default: str, type: str):
        at_start = True
        line_length = 0

        description_words = description.split()
        for word in description_words:
            line_length += 1 + len(word)

            if at_start:
                print("# ", end="")
                at_start = False

            print(f" {word}", end="")

            if line_length > MAX_LINE_LENGTH:
                at_start = True
                line_length = 0
                print("")
        print()

        if type == "string":
            default = f'"{default}"'
        elif type == "bool":
            default = "true" if default else "false"

        print(f"{name} = {default}")
        print("")

    def execute(self) -> None:
        # Assume you are in a directory which contains a terraform directory
        # which contains a variables.tf file.
        try:
            import hcl2
        except ImportError as ex:
            warnings.warn(
                "Need hcl2 module installed. Try pip install -r requirements-dev.txt"
            )
            raise ex

        with open(MAIN_VARIABLES_FILE, encoding="utf8") as variables_file:
            obj = hcl2.load(variables_file)
            for variable in obj["variable"]:
                for var_name in variable:
                    self._print_single_variable(
                        name=var_name,
                        description=variable[var_name]["description"],
                        default=variable[var_name].get("default", None),
                        type=variable[var_name]["type"],
                    )
