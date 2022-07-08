import pytest
from threatexchange.cli.tests.e2e_test_helper import (
    ThreatExchangeCLIE2eHelper,
    te_cli,
)
from threatexchange.exchanges.clients.ncmec.hash_api import NCMECEnvironment


@pytest.fixture
def cli(
    te_cli: ThreatExchangeCLIE2eHelper,
) -> ThreatExchangeCLIE2eHelper:
    te_cli.COMMON_CALL_ARGS = ("config", "collab")
    return te_cli


def test_required_argument(cli: ThreatExchangeCLIE2eHelper) -> None:
    name = "A config name"
    cli.assert_cli_usage_error(("edit", "ncmec", "-C", name))
    cli.cli_call(
        "edit", "ncmec", "-C", name, f"--environment={NCMECEnvironment.test_NGO.name}"
    )
    cli.assert_cli_output((), expected_output=f"ncmec {name}")  # Defaults to list
    cli.assert_cli_output(("list",), expected_output=f"ncmec {name}")
