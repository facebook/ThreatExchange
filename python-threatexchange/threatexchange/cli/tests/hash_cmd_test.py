import tempfile
from threatexchange.cli.tests.e2e_test_helper import ThreatExchangeCLIE2eTest


class HashCommandTest(ThreatExchangeCLIE2eTest):

    COMMON_CALL_ARGS = ("hash",)

    def test(self):
        self.assert_cli_output(
            ("url", "--inline", "http://evil.com"),
            "url_md5 6d3af727a4e7b025fd59a5469b3a9c57",
        )

        with tempfile.NamedTemporaryFile() as fp:
            # Empty file
            self.assert_cli_output(
                ("video", fp.name), "video_md5 d41d8cd98f00b204e9800998ecf8427e"
            )

        self.assert_cli_error_output(
            ("url", "blah.txt"),
            "The file blah.txt doesn't exist or the file path is incorrect",
        )
