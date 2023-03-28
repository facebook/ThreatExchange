# Copyright (c) Meta Platforms, Inc. and affiliates.

import tempfile
from threatexchange.cli.tests.e2e_test_helper import ThreatExchangeCLIE2eTest
from threatexchange.signal_type.md5 import VideoMD5Signal
from threatexchange.signal_type.pdq import PdqSignal


class MatchCommandTest(ThreatExchangeCLIE2eTest):
    COMMON_CALL_ARGS = ("match",)

    def test_file_noexst(self):
        self.assert_cli_usage_error(("text", "doesnt_exist.txt"))

    def test_match_file(self):
        with tempfile.NamedTemporaryFile() as fp:
            # Empty file
            self.assert_cli_output(
                ("video", fp.name), "video_md5 - (Sample Signals) INVESTIGATION_SEED"
            )

    def test_hash(self):
        hash = VideoMD5Signal.get_examples()[0]
        self.assert_cli_output(
            ("-H", "video", "--", hash),
            "video_md5 - (Sample Signals) INVESTIGATION_SEED",
        )

    def test_invalid_hash(self):
        not_hash = "this is not an md5"
        self.assert_cli_usage_error(
            ("-H", "video", "--", not_hash),
            f"'{not_hash.split()[0]}' is not a valid hash for video_md5",
        )

    def test_valid_hash_with_prefix(self):
        hash = "pdq " + PdqSignal.get_examples()[0]
        self.assert_cli_output(
            ("-H", "photo", "--", hash), "pdq 16 (Sample Signals) INVESTIGATION_SEED"
        )

    def test_no_prefix_specific_signal_type(self):
        hash = PdqSignal.get_examples()[0]
        self.assert_cli_output(
            ("-H", "-S", "pdq", "photo", "--", hash),
            "pdq 16 (Sample Signals) INVESTIGATION_SEED",
        )

    def test_multiple_prefixes(self):
        hash1 = "pdq " + PdqSignal.get_examples()[0]
        hash2 = "pdq " + PdqSignal.get_examples()[1]
        with tempfile.NamedTemporaryFile("a+") as fp:
            fp.write(hash1 + "\n")
            fp.write(hash2)
            fp.seek(0)
            # CLI is currently showing only one match for multiple hashes
            # TODO Improve the handling of multiple hashes in one match query
            self.assert_cli_output(
                ("-H", "photo", fp.name), "pdq 16 (Sample Signals) INVESTIGATION_SEED"
            )

    def test_incorrect_valid_and_no_prefixes(self):
        fakeprefix = "fakesignal"
        hash1 = "pdq " + PdqSignal.get_examples()[0]
        hash2 = fakeprefix + " " + PdqSignal.get_examples()[1]
        hash3 = fakeprefix + " " + PdqSignal.get_examples()[2]
        with tempfile.NamedTemporaryFile("a+") as fp:
            fp.write(hash1 + "\n")
            fp.write(hash2 + "\n")
            fp.write(hash3)
            fp.seek(0)
            self.assert_cli_usage_error(
                ("-H", "photo", fp.name),
                f"Error: '{fakeprefix}' is not a valid Signal Type.*",
            )

    def test_prefix_and_no_prefixes(self):
        hash1 = "pdq " + PdqSignal.get_examples()[0]
        hash2 = "pdq " + PdqSignal.get_examples()[1]
        hash3 = PdqSignal.get_examples()[1]
        with tempfile.NamedTemporaryFile("a+") as fp:
            fp.write(hash1 + "\n")
            fp.write(hash2 + "\n")
            fp.write(hash3)
            fp.seek(0)
            # CLI is currently showing only one match for multiple hashes
            # TODO Improve the handling of multiple hashes in one match query
            self.assert_cli_output(
                ("-H", "photo", fp.name), "pdq 16 (Sample Signals) INVESTIGATION_SEED"
            )
