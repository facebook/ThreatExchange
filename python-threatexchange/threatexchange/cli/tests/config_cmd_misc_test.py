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
    te_cli.COMMON_CALL_ARGS = ("config",)
    return te_cli


def test_config_signal(cli: ThreatExchangeCLIE2eHelper) -> None:
    expected = [
        "pdq threatexchange.signal_type.pdq.signal.PdqSignal",
        "raw_text threatexchange.signal_type.raw_text.RawTextSignal",
        "trend_query threatexchange.signal_type.trend_query.TrendQuerySignal",
        "url threatexchange.signal_type.url.URLSignal",
        "url_md5 threatexchange.signal_type.url_md5.UrlMD5Signal",
        "video_md5 threatexchange.signal_type.md5.VideoMD5Signal",
    ]
    cli.assert_cli_output(["signal"], expected)
    cli.assert_cli_output(["signal", "list"], expected)


def test_config_content(cli: ThreatExchangeCLIE2eHelper) -> None:
    expected = [
        "photo threatexchange.content_type.photo.PhotoContent",
        "text threatexchange.content_type.text.TextContent",
        "url threatexchange.content_type.url.URLContent",
        "video threatexchange.content_type.video.VideoContent",
    ]
    cli.assert_cli_output(["content"], expected)
    cli.assert_cli_output(["content", "list"], expected)
