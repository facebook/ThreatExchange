# Copyright (c) Meta Platforms, Inc. and affiliates.

from threatexchange.cli import command_base
from threatexchange.cli.api_fb_threatexchange_cmd import ApiFBThreatExchangeCommand


class ApiCommand(command_base.CommandWithSubcommands):
    """
    Interact directly with an exchange's API.

    Unlike fetch -> match, these commands don't read or write the local store.
    Each exchange has its own commands, in its own terms.

    Example commands:

    ```
    $ threatexchange api fb_threatexchange query --help
    ```
    """

    _SUBCOMMANDS = [ApiFBThreatExchangeCommand]

    @classmethod
    def get_name(cls) -> str:
        return "api"
