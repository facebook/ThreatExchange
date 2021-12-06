##!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Common helpers and libraries for the all-in-one command.

Strongly consider moving classes and functions out of this file if it starts
to fill up.
"""

import argparse
import sys
import typing as t

from .. import common
from ..api import ThreatExchangeAPI
from ..dataset import Dataset


class CommandError(Exception):
    """Wrapper for exceptions which cause return codes"""

    def __init__(self, message: str, returncode: int = 1) -> None:
        super().__init__(message)
        self.returncode = returncode


class Command:
    """
    Simple wrapper around setting up commands for an argparse-based cli.
    """

    @classmethod
    def add_command_to_subparser(cls, subparsers) -> None:
        """
        Shortcut for adding the command to the parser.

        Propbably don't override.
        """
        command_ap = subparsers.add_parser(
            cls.get_name(),
            description=cls.get_description(),
            help=cls.get_help(),
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        command_ap.set_defaults(command_cls=cls)
        cls.init_argparse(command_ap)

    @classmethod
    def init_argparse(cls, argparse: argparse.ArgumentParser) -> None:
        """
        Program the command subparser for __init__

        Your argument names should match the argument names in __init__.
        Be careful of collisions with the top level arg names from all_in_one.py
        """
        pass

    @classmethod
    def get_name(cls) -> str:
        """The display name of the command"""
        return common.class_name_to_human_name(cls.__name__, "Command").replace(
            "_", "-"
        )

    @classmethod
    def get_description(self) -> str:
        """The long help of the command"""
        return self.__doc__ or ""

    @classmethod
    def get_help(cls) -> str:
        """The short help of the command"""
        line = cls.get_description().strip().partition("\n")[0]
        # Good luck debugging this! Slightly reformat short description
        # (toplevel --help)
        if line[0].isupper():
            first_word, sp, rem = line.partition(" ")
            line = f"{first_word.lower()}{sp}{rem}"
        if line[-1] == ".":
            line = line[:-1]
        return line

    @staticmethod
    def stderr(*args, **kwargs) -> None:
        """Convenience accessor to stderr"""
        print(*args, file=sys.stderr, **kwargs)

    def execute(self, api: ThreatExchangeAPI, dataset: Dataset) -> None:
        raise NotImplementedError
