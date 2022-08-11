from threatexchange.cli.tests.e2e_test_helper import ThreatExchangeCLIE2eTest

from threatexchange.cli.main import _DEFAULT_SIGNAL_TYPES


class DatasetCommandTest(ThreatExchangeCLIE2eTest):
    def test(self):
        """
        Test on the output of the dataset command, using the sample signals

        The sample signals will probably change a few times during the course
        of development, which will unexpectedly break this test, so apologies
        future developers.
        """
        signal_count = sum(len(st.get_examples()) for st in _DEFAULT_SIGNAL_TYPES)

        # Since we didn't set a collab config, this will fetch on first call
        self.assert_cli_output(
            ("dataset",),
            [
                "pdq: 16",
                "raw_text: 3",
                "video_md5: 2",
                "trend_query: 1",
                "url: 1",
                "url_md5: 1",
            ],
        )
        self.assert_cli_output(
            ("dataset", "--signal-summary"),
            [
                "pdq: 16",
                "raw_text: 3",
                "video_md5: 2",
                "trend_query: 1",
                "url: 1",
                "url_md5: 1",
            ],
        )

        # The sort of printed output is currently not stable
        output = self.cli_call("dataset", "-P")
        assert output.count("\n") == signal_count
        assert (
            "url "
            "https://developers.facebook.com/docs/threat-exchange/reference/apis/ "
            "'Sample Signals' "
            "INVESTIGATION_SEED"
        ) in output
        # The filters change the print output
        self.assert_cli_output(
            ("dataset", "-P", "-s", "url"),
            "https://developers.facebook.com/docs/threat-exchange/reference/apis/ "
            "'Sample Signals' "
            "INVESTIGATION_SEED",
        )
        self.assert_cli_output(
            ("dataset", "-P", "-s", "url", "-c", "Sample Signals"),
            "https://developers.facebook.com/docs/threat-exchange/reference/apis/ "
            "INVESTIGATION_SEED",
        )
        self.assert_cli_output(
            ("dataset", "-P", "-s", "url", "-S"),
            "https://developers.facebook.com/docs/threat-exchange/reference/apis/",
        )
        # CSV stuff
        output = self.cli_call("dataset", "-P", "--csv")
        assert output.count("\n") - 1 == signal_count  # -1 for header
        assert (
            "url,"
            "https://developers.facebook.com/docs/threat-exchange/reference/apis/,"
            "Sample Signals,"
            "INVESTIGATION_SEED,"
        ) in output
        # Repeat same filters - however, these don't change the output format except -S\
        csv_header = "signal_type,signal_str,collab,category,tags\n"
        self.assert_cli_output(
            ("dataset", "-P", "--csv", "-s", "url"),
            csv_header + "url,"
            "https://developers.facebook.com/docs/threat-exchange/reference/apis/,"
            "Sample Signals,INVESTIGATION_SEED,",
        )
        self.assert_cli_output(
            ("dataset", "-P", "--csv", "-s", "url", "-c", "Sample Signals"),
            csv_header + "url,"
            "https://developers.facebook.com/docs/threat-exchange/reference/apis/,"
            "Sample Signals,INVESTIGATION_SEED,",
        )
        # --csv and -S not combinable
        self.assert_cli_usage_error(("dataset", "-P", "--csv", "-S"))

    def test_indices(self):
        self.cli_call("fetch", "--skip-index-rebuild")
        self.cli_call("dataset", "-r")  # Someday actually test?
