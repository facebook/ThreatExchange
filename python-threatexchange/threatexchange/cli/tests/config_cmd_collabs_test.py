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


def test_editing_collab(cli: ThreatExchangeCLIE2eHelper) -> None:
    name = "collab_name"
    expected = """
{
  "environment": "%s",
  "name": "collab_name",
  "api": "ncmec",
  "enabled": true,
  "only_esp_ids": []
}
    """.strip()
    cli.cli_call(
        "edit",
        "ncmec",
        "-C",
        name,
        f"--environment={NCMECEnvironment.test_NGO.name}",
    )
    cli.assert_cli_output(["print", name], expected % NCMECEnvironment.test_NGO.value)
    cli.cli_call(
        "edit",
        "ncmec",
        name,
        f"--environment={NCMECEnvironment.test_Exploitative.name}",
    )

    cli.assert_cli_output(
        ["print", name], expected % NCMECEnvironment.test_Exploitative.value
    )


def test_complex_types(cli: ThreatExchangeCLIE2eHelper) -> None:
    cli.cli_call(
        "tx",
        "config",
        "extensions",
        "add",
        "threatexchange.cli.tests.fake_extension",
    )
    cli.cli_call(
        "edit",
        "fake",
        "fake",
        "--an-int=1",
        "--a-str=a",
        "--an-enum=OPTION_A",
        "--a-list=1,2,3",
        "--a-set=3,2",
        "--create",
    )
    expected = """
{
  "an_int": 1,
  "a_str": "a",
  "a_list": [
    "1",
    "2",
    "3"
  ],
  "a_set": [
    2,
    3
  ],
  "an_enum": "a",
  "name": "fake",
  "api": "fake",
  "enabled": true,
  "optional": null
}
    """.strip()
    cli.assert_cli_output(["print", "fake"], expected)
