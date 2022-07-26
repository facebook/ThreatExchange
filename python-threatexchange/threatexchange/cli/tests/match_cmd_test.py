import tempfile
from threatexchange.cli.tests.e2e_test_helper import ThreatExchangeCLIE2eTest
from threatexchange.signal_type.md5 import VideoMD5Signal


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
            f"{not_hash!r} from .* is not a valid hash for video_md5",
        )
