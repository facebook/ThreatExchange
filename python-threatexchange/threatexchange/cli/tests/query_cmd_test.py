# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Tests for `threatexchange query`, against a fake of the Graph API's
/threat_descriptors edge that applies the documented filters.

The fake is only as accurate as our reading of Meta's documentation. These
tests show that the CLI sends what it means to, pages, and formats correctly;
not how Meta's servers behave.
"""

import csv
import io
import json
import pathlib
import threading
import typing as t
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from threatexchange.cli.exceptions import CommandError
from threatexchange.cli.query_cmd import QueryCommand
from threatexchange.cli.tests.e2e_test_helper import (
    E2ETestSystemExit,
    ThreatExchangeCLIE2eHelper,
    te_cli,  # noqa: F401 - pytest fixture
)
from threatexchange.exchanges.clients.fb_threatexchange.api import ThreatExchangeAPI

PG = 111


def _descriptor(
    id: int,
    indicator: str,
    *,
    type: str = "HASH_PDQ",
    status: str = "MALICIOUS",
    tags: t.Sequence[str] = (),
    owner: int = 900,
    confidence: int = 50,
    time: int = 1_700_000_000,
    pg: int = PG,
) -> t.Dict[str, t.Any]:
    return {
        "id": str(id),
        "raw_indicator": indicator,
        "type": type,
        "status": status,
        "tags": list(tags),
        "owner": owner,
        "confidence": confidence,
        "added_on": time,
        "description": f"about {indicator}",
        "_pg": pg,
    }


DESCRIPTORS = [
    _descriptor(1, "aaa", tags=["csam", "photo"], owner=900, confidence=90, time=1000),
    _descriptor(2, "bbb", tags=["csam"], owner=901, confidence=60, time=2000),
    _descriptor(3, "ccc", tags=["photo"], owner=900, confidence=10, time=3000),
    _descriptor(
        4, "ddd", type="HASH_MD5", status="NON_MALICIOUS", owner=903, time=4000
    ),
    _descriptor(5, "eee", tags=["csam"], owner=902, confidence=80, time=5000),
    _descriptor(6, "fff", tags=["csam", "photo"], owner=900, time=6000, pg=222),
]


class _FakeGraph:
    def __init__(self) -> None:
        self.queries: t.List[t.Dict[str, str]] = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                url = urllib.parse.urlparse(self.path)
                q = dict(urllib.parse.parse_qsl(url.query))
                outer.queries.append(q)
                if url.path != "/v99.0/threat_descriptors":
                    return self._send(404, {"error": {"message": "no", "code": 803}})
                if q.get("status") == "BOGUS":
                    return self._send(
                        400,
                        {"error": {"message": "Invalid StatusType BOGUS", "code": 100}},
                    )
                self._send(200, outer.answer(q, url.path))

            def _send(self, status: int, body: t.Any) -> None:
                raw = json.dumps(body).encode()
                self.send_response(status)
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def log_message(self, *args: t.Any) -> None:
                pass

        self.httpd = HTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.httpd.server_address[1]}/v99.0"

    def close(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join()

    def answer(self, q: t.Dict[str, str], path: str) -> t.Dict[str, t.Any]:
        def csv_ints(key: str) -> t.Optional[t.Set[int]]:
            return {int(x) for x in q[key].split(",")} if key in q else None

        pgs, owners = csv_ints("privacy_groups"), csv_ints("owner")
        want_tags = set(q["tags"].split(",")) if "tags" in q else None
        results = []
        for d in DESCRIPTORS:
            if pgs is not None and d["_pg"] not in pgs:
                continue
            if owners is not None and d["owner"] not in owners:
                continue
            if want_tags is not None:
                have = set(d["tags"])
                if q.get("tags_are_anded") == "true":
                    if not want_tags <= have:
                        continue
                elif not want_tags & have:
                    continue
            if "status" in q and d["status"] != q["status"]:
                continue
            if "type" in q and d["type"] != q["type"]:
                continue
            if "since" in q and d["added_on"] <= int(q["since"]):
                continue
            if "until" in q and d["added_on"] >= int(q["until"]):
                continue
            if "min_confidence" in q and d["confidence"] < int(q["min_confidence"]):
                continue
            if "max_confidence" in q and d["confidence"] > int(q["max_confidence"]):
                continue
            results.append(d)

        limit = min(int(q.get("limit", 25)), 1000)
        offset = int(q.get("after", 0))
        page = results[offset : offset + limit]
        body: t.Dict[str, t.Any] = {"data": [self.project(d, q) for d in page]}
        if offset + limit < len(results):
            nq = dict(q, after=str(offset + limit))
            host = f"127.0.0.1:{self.httpd.server_address[1]}"
            body["paging"] = {
                "next": f"http://{host}{path}?{urllib.parse.urlencode(nq)}"
            }
        return body

    @staticmethod
    def project(d: t.Dict[str, t.Any], q: t.Dict[str, str]) -> t.Dict[str, t.Any]:
        """Return only the requested fields, in the shapes the Graph API uses"""
        ret: t.Dict[str, t.Any] = {"id": d["id"]}
        for field in q.get("fields", "").split(","):
            if field == "owner{id}":
                ret["owner"] = {"id": str(d["owner"])}
            elif field == "tags":
                ret["tags"] = {
                    "data": [{"id": "1", "text": tag} for tag in d["tags"][::-1]]
                }
            elif field in d and not field.startswith("_"):
                ret[field] = d[field]
        return ret


@pytest.fixture
def graph(monkeypatch: pytest.MonkeyPatch) -> t.Iterator[_FakeGraph]:
    fake = _FakeGraph()
    monkeypatch.setattr(
        QueryCommand,
        "get_te_api",
        lambda self: ThreatExchangeAPI("123|token", endpoint_override=fake.base_url),
    )
    yield fake
    fake.close()


def _rows(output: str) -> t.List[t.Dict[str, str]]:
    return list(csv.DictReader(io.StringIO(output)))


def _query(
    te_cli: ThreatExchangeCLIE2eHelper, *args: str  # noqa: F811
) -> t.List[t.Dict[str, str]]:
    return _rows(te_cli.cli_call("query", *args))


def _indicators(rows: t.List[t.Dict[str, str]]) -> t.List[str]:
    return [r["indicator"] for r in rows]


def test_default_columns(te_cli, graph):  # noqa: F811
    rows = _query(te_cli, "--privacy-group", str(PG))
    assert list(rows[0]) == ["id", "indicator", "type", "status", "tags", "owner_id"]
    assert rows[0] == {
        "id": "1",
        "indicator": "aaa",
        "type": "HASH_PDQ",
        "status": "MALICIOUS",
        "tags": "csam photo",  # Sorted, whatever order the API used
        "owner_id": "900",
    }
    assert _indicators(rows) == ["aaa", "bbb", "ccc", "ddd", "eee"]  # Not group 222


@pytest.mark.parametrize(
    "args,expected",
    [
        (["--tags", "csam"], ["aaa", "bbb", "eee"]),
        (["--tags", "csam", "photo"], ["aaa", "bbb", "ccc", "eee"]),
        (["--tags", "csam", "photo", "--tags-all"], ["aaa"]),
        (["--status", "non_malicious"], ["ddd"]),
        (["--owner", "900"], ["aaa", "ccc"]),
        (["--owner", "901", "902"], ["bbb", "eee"]),
        (["--type", "hash_md5"], ["ddd"]),
        (["--since", "2000"], ["ccc", "ddd", "eee"]),
        (["--until", "3000"], ["aaa", "bbb"]),
        (["--since", "1970-01-01T00:16:40", "--until", "1970-01-01T00:50:00"], ["bbb"]),
        (["--min-confidence", "60"], ["aaa", "bbb", "eee"]),
        (["--max-confidence", "50"], ["ccc", "ddd"]),
        # Filters are ANDed
        (
            ["--tags", "csam", "--owner", "900", "901", "--min-confidence", "70"],
            ["aaa"],
        ),
        (["--tags", "nonexistent"], []),
    ],
)
def test_filters(te_cli, graph, args, expected):  # noqa: F811
    rows = _query(te_cli, "--privacy-group", str(PG), *args)
    assert _indicators(rows) == expected


def test_only_requested_options_are_sent(te_cli, graph):  # noqa: F811
    _query(te_cli, "--tags", "csam")
    (q,) = graph.queries
    assert set(q) == {"access_token", "tags", "limit", "fields"}
    assert q["limit"] == "1000"


def test_options_are_sent_to_the_api(te_cli, graph):  # noqa: F811
    _query(
        te_cli,
        "--privacy-group", "1", "2",
        "--text", "abc",
        "--strict-text",
        "--tags", "x", "y",
        "--tags-all",
        "--status", "malicious",
        "--owner", "7", "8",
        "--type", "hash_pdq",
        "--since", "10",
        "--until", "20",
        "--min-confidence", "0",
        "--max-confidence", "100",
        "--review-status", "reviewed_manually",
        "--share-level", "amber",
        "--include-expired",
        "--sort-by", "create_time",
    )  # fmt: skip
    (q,) = graph.queries
    q.pop("access_token")
    assert q == {
        "privacy_groups": "1,2",
        "text": "abc",
        "strict_text": "true",  # Not Python's "True"
        "tags": "x,y",
        "tags_are_anded": "true",
        "status": "MALICIOUS",
        "owner": "7,8",
        "type": "HASH_PDQ",
        "since": "10",
        "until": "20",
        "min_confidence": "0",  # Zero is a value, not "unset"
        "max_confidence": "100",
        "review_status": "REVIEWED_MANUALLY",
        "share_level": "AMBER",
        "sort_by": "CREATE_TIME",
        "include_expired": "true",
        "limit": "1000",
        "fields": "id,raw_indicator,type,status,tags,owner{id}",
    }


def test_columns_request_only_their_fields(te_cli, graph):  # noqa: F811
    rows = _query(te_cli, "--columns", "indicator,owner_id,description,tags")
    (q,) = graph.queries
    assert q["fields"] == "raw_indicator,owner{id},description,tags"
    assert list(rows[0]) == ["indicator", "owner_id", "description", "tags"]
    assert rows[0]["description"] == "about aaa"


def test_paging(te_cli, graph):  # noqa: F811
    rows = _query(te_cli, "--privacy-group", str(PG), "--page-size", "2")
    assert _indicators(rows) == ["aaa", "bbb", "ccc", "ddd", "eee"]
    assert len(graph.queries) == 3  # 2 + 2 + 1


def test_limit_stops_early(te_cli, graph):  # noqa: F811
    rows = _query(te_cli, "--page-size", "2", "--limit", "4")
    assert len(rows) == 4
    assert len(graph.queries) == 2  # Didn't fetch a third page


def test_small_limit_shrinks_page_size(te_cli, graph):  # noqa: F811
    _query(te_cli, "--limit", "3")
    assert graph.queries[0]["limit"] == "3"


def test_collab_resolves_to_privacy_group(te_cli, graph):  # noqa: F811
    te_cli.cli_call(
        "config",
        "collab",
        "edit",
        "fb_threatexchange",
        "--create",
        "Marc",
        "--privacy-group",
        str(PG),
    )
    rows = _query(te_cli, "-c", "Marc", "--tags", "photo")
    assert graph.queries[0]["privacy_groups"] == str(PG)
    assert _indicators(rows) == ["aaa", "ccc"]

    # Combined with explicit groups, deduped
    _query(te_cli, "-c", "Marc", "-g", str(PG), "222")
    assert graph.queries[1]["privacy_groups"] == f"{PG},222"


def test_unknown_collab(te_cli, graph):  # noqa: F811
    te_cli.assert_cli_usage_error(("query", "-c", "Nope"), "No such collab")
    assert graph.queries == []


def test_jsonl_and_output_file(te_cli, graph, tmp_path: pathlib.Path):  # noqa: F811
    out = tmp_path / "out.jsonl"
    stdout = te_cli.cli_call(
        "query", "--format", "jsonl", "--tags", "csam", "photo", "-o", str(out)
    )
    assert stdout == ""
    lines = [json.loads(line) for line in out.read_text().splitlines()]
    assert lines[0] == {
        "id": "1",
        "indicator": "aaa",
        "type": "HASH_PDQ",
        "status": "MALICIOUS",
        "tags": ["csam", "photo"],  # A real list, not a joined string
        "owner_id": "900",
    }
    # No group given, so this includes group 222's "fff" too
    assert [line["indicator"] for line in lines] == ["aaa", "bbb", "ccc", "eee", "fff"]


def test_api_errors_show_the_reason(te_cli, graph):  # noqa: F811
    with pytest.raises(CommandError, match="error 100: Invalid StatusType BOGUS") as e:
        te_cli.cli_call("query", "--status", "bogus")
    assert e.value.returncode == 3


def test_list_columns(te_cli, graph):  # noqa: F811
    out = te_cli.cli_call("query", "--list-columns")
    assert "owner_id" in out and "raw_indicator" in out
    assert graph.queries == []


@pytest.mark.parametrize(
    "args",
    [
        ["--tags-all"],
        ["--strict-text"],
        ["--limit", "0"],
        ["--columns", "indicator,bogus"],
        ["--page-size", "1001"],
        ["--since", "yesterday"],
        ["--sort-by", "random"],
    ],
)
def test_bad_arguments(te_cli, graph, args):  # noqa: F811
    with pytest.raises((CommandError, E2ETestSystemExit)) as e:
        te_cli.cli_call("query", *args)
    assert e.value.returncode == 2
    assert graph.queries == []
