# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

from threatexchange.cli import main
from threatexchange.cli.tests.e2e_test_helper import ThreatExchangeCLIE2eTest


class CLISmokeTest(ThreatExchangeCLIE2eTest):
    def test_all_helps(self):
        """
        Just executes all the commands to make sure they don't throw on help.

        View the pretty output with py.test -s
        """
        self.cli_call()  # root help
        self.cli_call("--help")  # root help
        for command in main.get_subcommands():
            self.cli_call(command.get_name(), "--help")
