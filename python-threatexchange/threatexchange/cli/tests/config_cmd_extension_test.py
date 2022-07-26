import pytest
from threatexchange.cli.tests.e2e_test_helper import (
    ThreatExchangeCLIE2eHelper,
    te_cli,
)


@pytest.fixture
def cli(
    te_cli: ThreatExchangeCLIE2eHelper,
) -> ThreatExchangeCLIE2eHelper:
    te_cli.COMMON_CALL_ARGS = ("config", "extensions")
    return te_cli


def test_extension_manipulate(cli: ThreatExchangeCLIE2eHelper) -> None:
    expected = [
        "Signal:",
        "  fake - FakeSignal",
        "Content:",
        "  fake - FakeContent",
        "Content:",
        "  fake - FakeSignalExchange",
    ]
    cli.assert_cli_output(["list"], "")
    cli.assert_cli_output(["add", "threatexchange.cli.tests.fake_extension"], expected)
    cli.assert_cli_output(
        ["list"],
        ["threatexchange.cli.tests.fake_extension"] + ["  " + e for e in expected],
    )
    cli.assert_cli_output(["list", "threatexchange.cli.tests.fake_extension"], expected)
    # Double add ok
    cli.assert_cli_output(["add", "threatexchange.cli.tests.fake_extension"], expected)

    cli.assert_cli_output(["remove", "threatexchange.cli.tests.fake_extension"], "")
    cli.assert_cli_output(["list"], "")

    # Double remove
    cli.assert_cli_usage_error(["remove", "threatexchange.cli.tests.fake_extension"])
    # Add noexist
    cli.assert_cli_usage_error(["list", "threatexchange.cli.tests.noexist"])


def test_extensions_in_other_cmds(cli: ThreatExchangeCLIE2eHelper) -> None:
    cli.cli_call("add", "threatexchange.cli.tests.fake_extension")
    cli.assert_cli_output(
        ["tx", "hash", "--signal-type=fake", "fake", "--", "lolol"], "fake fake"
    )
    cli.assert_cli_output(
        ["tx", "hash", "--signal-type=fake", "fake", "--", "lolol"], "fake fake"
    )
    cli.assert_cli_output(
        ["tx", "match", "--only-signal=fake", "fake", "--", "lolol"],
        "fake - (Sample Signals) INVESTIGATION_SEED",
    )
