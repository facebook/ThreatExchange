import io
import pathlib
import tempfile
import pytest
from threatexchange.cli.tests.e2e_test_helper import (
    ThreatExchangeCLIE2eHelper,
    te_cli,
)


@pytest.fixture
def hash_cli(
    te_cli: ThreatExchangeCLIE2eHelper,
) -> ThreatExchangeCLIE2eHelper:
    te_cli.COMMON_CALL_ARGS = ("hash",)
    return te_cli


@pytest.fixture
def tmp_file():
    with tempfile.NamedTemporaryFile() as f:
        yield pathlib.Path(f.name)


def test_file(hash_cli: ThreatExchangeCLIE2eHelper, tmp_file: pathlib.Path):
    tmp_file.write_text("http://evil.com")
    hash_cli.assert_cli_output(
        ("url", str(tmp_file)),
        "url_md5 6d3af727a4e7b025fd59a5469b3a9c57",
    )

    hash_cli.assert_cli_usage_error(("url", "blah.txt"))


def test_dashdash(hash_cli: ThreatExchangeCLIE2eHelper):
    hash_cli.assert_cli_output(
        ("url", "--", "http://evil.com"),
        "url_md5 6d3af727a4e7b025fd59a5469b3a9c57",
    )


def test_stdin(
    hash_cli: ThreatExchangeCLIE2eHelper,
    monkeypatch: pytest.MonkeyPatch,
    tmp_file: pathlib.Path,
):
    tmp_file.write_text("http://evil.com")

    with tmp_file.open() as fake_stin:
        monkeypatch.setattr("sys.stdin", fake_stin)
        hash_cli.assert_cli_output(
            ("url", "-"),
            "url_md5 6d3af727a4e7b025fd59a5469b3a9c57",
        )


def test_mixed(hash_cli: ThreatExchangeCLIE2eHelper, tmp_path: pathlib.Path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    a.write_text("http://evil.com", None)
    b.touch()

    hash_cli.assert_cli_output(
        ("url", str(a), str(b), "--", "fb.com"),
        [
            "url_md5 6d3af727a4e7b025fd59a5469b3a9c57",
            "url_md5 d41d8cd98f00b204e9800998ecf8427e",
            "url_md5 fb8191ebebc85f9eb6fd21e198f20979",
        ],
    )


def test_missing(hash_cli: ThreatExchangeCLIE2eHelper):
    hash_cli.assert_cli_usage_error(())
    hash_cli.assert_cli_usage_error(("photo",))
