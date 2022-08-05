from threatexchange.cli.tests.e2e_test_helper import ThreatExchangeCLIE2eTest
from threatexchange.signal_type.raw_text import RawTextSignal


class SampleDataE2ETest(ThreatExchangeCLIE2eTest):
    """
    The CLI should demonstrate functionality with only sample data.
    """

    MATCHES_ONE = RawTextSignal.get_examples()[0]
    MATCHES_TWO = RawTextSignal.get_examples()[-1]

    def test_direct_to_match(self):
        """The classic first use of the CLI"""
        self.assert_cli_output(
            ("match", "text", "--", self.MATCHES_ONE),
            "raw_text 100% (Sample Signals) INVESTIGATION_SEED",
        )

    def test_sequential_to_match(self):
        """Same as the classic first use, broken to component parts"""
        self.cli_call("fetch")
        self.cli_call("dataset", "-r")
        self.assert_cli_output(
            ("match", "text", "--", self.MATCHES_ONE),
            "raw_text 100% (Sample Signals) INVESTIGATION_SEED",
        )

    def test_multiple_match(self):
        """Matches should be able to hit multiple types"""
        self.assert_cli_output(
            ("match", "text", "--", self.MATCHES_TWO),
            "\n".join(
                (
                    "raw_text 100% (Sample Signals) INVESTIGATION_SEED",
                    "trend_query - (Sample Signals) INVESTIGATION_SEED",
                ),
            ),
        )

    def test_no_labeling(self):
        """You can't label the sample dataset"""
        self.assert_cli_usage_error(("label", "Sample Signals", "text", "foo"))
