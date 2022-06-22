import pathlib
import pytest
from threatexchange.cli.tests.e2e_test_helper import ThreatExchangeCLIE2eHelper, te_cli


@pytest.fixture
def hash_cli(te_cli: ThreatExchangeCLIE2eHelper) -> ThreatExchangeCLIE2eHelper:
    te_cli.COMMON_CALL_ARGS = ("hash",)
    return te_cli


def test(hash_cli: ThreatExchangeCLIE2eHelper, tmp_path: pathlib.Path):
    hash_cli.assert_cli_output(
        ("url", "--inline", "http://evil.com"),
        "url_md5 6d3af727a4e7b025fd59a5469b3a9c57",
    )

    empty_file = tmp_path / "empty.mp4"
    empty_file.touch()

    hash_cli.assert_cli_output(
        ("video", str(empty_file)), "video_md5 d41d8cd98f00b204e9800998ecf8427e"
    )

    hash_cli.assert_cli_usage_error(
        ("url", "blah.txt"),
        "The file blah.txt doesn't exist or the file path is incorrect",
    )
