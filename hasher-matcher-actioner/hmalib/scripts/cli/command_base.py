##!/usr/bin/env python
# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Common interface for script commands that interface with HMA.
(based off of python-threatexchange CLI)
"""

import argparse
import sys
import typing as t

import hmalib.scripts.common.utils as utils


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

        Probably don't override.
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
        """
        pass

    @classmethod
    def get_name(cls) -> str:
        """The display name of the command"""
        raise NotImplementedError

    @classmethod
    def get_description(self) -> str:
        """The long help of the command"""
        return self.__doc__ or ""

    @classmethod
    def get_help(cls) -> str:
        """The short help of the command"""
        raise NotImplementedError

    @staticmethod
    def stderr(*args, **kwargs) -> None:
        """Convenience accessor to stderr"""
        print(*args, file=sys.stderr, **kwargs)


# Marker interfaces for main to figure out what to pass
class NeedsAPIAccess:
    def execute(self, api: utils.HasherMatcherActionerAPI) -> None:
        """
        Provide implementation for a command which needs access to the HMA API.
        """
        raise NotImplementedError


class NeedsTerraformOutputs:
    def execute(self, terraform_outputs: t.Dict) -> None:
        """
        Provide implementation for a command which needs access to terraform
        output only.
        """
        raise NotImplementedError
