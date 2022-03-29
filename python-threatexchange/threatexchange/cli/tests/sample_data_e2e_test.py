from threatexchange.cli.tests.e2e_test_helper import ThreatExchangeCLIE2eTest


class SampleDataE2ETest(ThreatExchangeCLIE2eTest):
    """
    The CLI should demonstrate functionality with only sample data.
    """

    def test_sequential_to_match(self):
        self.cli_call("fetch")
        self.cli_call("dataset", "-r")
        self.assert_cli_output(
            ("match", "text", "-I", "bball now?"),
            "raw_text - (Sample Signals) WORTH_INVESTIGATING",
        )

    def test_direct_to_match(self):
        self.assert_cli_output(
            ("match", "text", "-I", "bball now?"),
            "raw_text - (Sample Signals) WORTH_INVESTIGATING",
            -1,
        )

    def test_no_labeling(self):
        self.assert_cli_usage_error(("label", "Sample Signals", "text", "foo"))
