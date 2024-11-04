# Copyright (c) Meta Platforms, Inc. and affiliates.

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


def test_rotations_with_non_photo_content(
    hash_cli: ThreatExchangeCLIE2eHelper, tmp_file: pathlib.Path
):
    """Test that rotation flag raises error with non-photo content"""
    for content_type in ["url", "text", "video"]:
        hash_cli.assert_cli_usage_error(
            ("--rotations", content_type, str(tmp_file)),
            msg_regex="--rotations flag is only available for Photo content type",
        )


def test_rotations_with_photo_content(hash_cli: ThreatExchangeCLIE2eHelper):
    """Test that photo rotations are properly processed"""
    test_file = pathlib.Path("threatexchange/tests/hashing/resources/LA.png")

    hash_cli.assert_cli_output(
        ("--rotations", "photo", str(test_file)),
        [
            "ORIGINAL pdq accb6d39648035f8125c8ce6ba65007de7b54c67a2d93ef7b8f33b0611306715",
            "ROTATE90 pdq 1f70cbbc77edc5f9524faa1b18f3b76cd0a04a833e20f645d229d0acc8499c56",
            "ROTATE180 pdq 31ddf2513558de0ae56e4a8c8930cadde2ee084df3aed0a75fa512ea0e41e197",
            "ROTATE270 pdq c79931968e880f4b97196df4d5ea0fb489b99e2c10af0dceacf572809b815ea5",
            "FLIPX pdq aaca8605440c4a6735dbbf59b947df92e7bf161807e9cd88baf04579523098ab",
            "FLIPY pdq 559f78de2530abbdc663b131ed78f10072c4bb13f3acd6017d0e69150e413e5a",
            "FLIPPLUS1 pdq 86a860c1f2bd1a1ec65cf4d10ab55087b4b89f7857da59bbd9200fd5845cc3f9",
            "FLIPMINUS1 pdq 5bb15db9e8a1f03c174a380a55aeaa2985bde9c60abce301bde48df918b5c15b",
        ],
    )
