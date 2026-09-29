# Copyright (c) Meta Platforms, Inc. and affiliates.

import argparse
import csv
import datetime
import json
import sys
import typing as t

import requests

from threatexchange.cli import command_base
from threatexchange.cli.cli_config import CLISettings
from threatexchange.cli.exceptions import CommandError
from threatexchange.exchanges.clients.fb_threatexchange.api import ThreatExchangeAPI
from threatexchange.exchanges.impl.fb_threatexchange_api import (
    FBThreatExchangeCollabConfig,
    FBThreatExchangeCredentials,
    FBThreatExchangeSignalExchangeAPI,
)

_MAX_PAGE_SIZE = 1000  # https://developers.facebook.com/docs/threat-exchange/reference/apis/threat-descriptors/


def _tags(descriptor: t.Dict[str, t.Any]) -> t.List[str]:
    tags = descriptor.get("tags") or []
    if isinstance(tags, dict):  # {"data": [{"id": ..., "text": ...}]}
        return sorted(tag["text"] for tag in tags.get("data", []))
    return sorted(tags)


def _owner_id(descriptor: t.Dict[str, t.Any]) -> t.Any:
    return (descriptor.get("owner") or {}).get("id", "")


def _plain(field: str) -> t.Tuple[str, t.Callable[[t.Dict[str, t.Any]], t.Any]]:
    return field, lambda d: d.get(field, "")


# column name => (ThreatDescriptor field to request, how to read it)
_COLUMNS: t.Dict[str, t.Tuple[str, t.Callable[[t.Dict[str, t.Any]], t.Any]]] = {
    "id": _plain("id"),
    "indicator": ("raw_indicator", lambda d: d.get("raw_indicator", "")),
    "type": _plain("type"),
    "status": _plain("status"),
    "tags": ("tags", _tags),
    "owner_id": ("owner{id}", _owner_id),
    "confidence": _plain("confidence"),
    "severity": _plain("severity"),
    "review_status": _plain("review_status"),
    "share_level": _plain("share_level"),
    "privacy_type": _plain("privacy_type"),
    "added_on": _plain("added_on"),
    "last_updated": _plain("last_updated"),
    "description": _plain("description"),
}
_DEFAULT_COLUMNS = ["id", "indicator", "type", "status", "tags", "owner_id"]


def _timestamp(s: str) -> int:
    """Unix seconds, or an ISO date/time (UTC if no timezone given)"""
    try:
        return int(s)
    except ValueError:
        pass
    try:
        when = datetime.datetime.fromisoformat(s)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"{s!r}: use unix seconds or an ISO date like 2026-01-31 or 2026-01-31T12:00"
        )
    if when.tzinfo is None:
        when = when.replace(tzinfo=datetime.timezone.utc)
    return int(when.timestamp())


def _page_size(s: str) -> int:
    n = int(s)
    if not 1 <= n <= _MAX_PAGE_SIZE:
        raise argparse.ArgumentTypeError(f"must be between 1 and {_MAX_PAGE_SIZE}")
    return n


def _columns(s: str) -> t.List[str]:
    cols = [c.strip() for c in s.split(",") if c.strip()]
    bad = [c for c in cols if c not in _COLUMNS]
    if bad or not cols:
        raise argparse.ArgumentTypeError(
            f"unknown column(s) {bad}. Choose from: {', '.join(_COLUMNS)}"
        )
    return cols


class QueryCommand(command_base.Command):
    """
    Search Meta's ThreatExchange API and write the results as CSV.

    Filtering happens on Meta's servers, so only matching descriptors are
    downloaded. Nothing is stored locally, and it doesn't use `fetch`.
    Use `fetch` and `dataset` instead to keep a full local copy.

    Needs a ThreatExchange access token, see
      $ threatexchange config api fb_threatexchange --help

    All the filters are ANDed. Values are as defined by Meta:
    https://developers.facebook.com/docs/threat-exchange/reference/apis/threat-descriptors/

    Example commands:

    ```
    # Everything in a configured collaboration tagged 'csam', as a CSV
    $ threatexchange query -c 'My Collab' --tags csam -o csam.csv

    # PDQ hashes that a specific member marked malicious, since the start of the year
    $ threatexchange query --privacy-group 1234 --type HASH_PDQ \\
        --status MALICIOUS --owner 5678 --since 2026-01-01 \\
        --columns indicator,tags,added_on

    # See the columns available
    $ threatexchange query --list-columns
    ```
    """

    @classmethod
    def init_argparse(cls, settings: CLISettings, ap: argparse.ArgumentParser) -> None:
        where = ap.add_argument_group("where to search")
        where.add_argument(
            "--collab",
            "-c",
            dest="collabs",
            nargs="+",
            default=[],
            metavar="NAME",
            help="search the privacy groups of these fb_threatexchange collabs",
        )
        where.add_argument(
            "--privacy-group",
            "-g",
            dest="privacy_groups",
            nargs="+",
            type=int,
            default=[],
            metavar="ID",
            help="search these ThreatPrivacyGroup ids. "
            "With neither this nor --collab, searches everything your app can see",
        )

        flt = ap.add_argument_group("filters")
        flt.add_argument("--text", help="free text to search for, e.g. a hash")
        flt.add_argument(
            "--strict-text",
            action="store_true",
            help="[--text] exact matches only, no approximate matching",
        )
        flt.add_argument(
            "--tags", nargs="+", default=[], metavar="TAG", help="having any of these"
        )
        flt.add_argument(
            "--tags-all",
            action="store_true",
            help="[--tags] require all the tags rather than any",
        )
        flt.add_argument(
            "--status", type=str.upper, help="e.g. MALICIOUS, NON_MALICIOUS"
        )
        flt.add_argument(
            "--owner",
            dest="owners",
            nargs="+",
            type=int,
            default=[],
            metavar="APP_ID",
            help="uploaded by any of these ThreatExchange member (app) ids",
        )
        flt.add_argument(
            "--type",
            dest="indicator_type",
            type=str.upper,
            metavar="TYPE",
            help="indicator type, e.g. HASH_PDQ, HASH_MD5, URI",
        )
        flt.add_argument(
            "--since",
            type=_timestamp,
            metavar="WHEN",
            help="collected after this unix time or ISO date/time (UTC)",
        )
        flt.add_argument(
            "--until",
            type=_timestamp,
            metavar="WHEN",
            help="collected before this unix time or ISO date/time (UTC)",
        )
        flt.add_argument("--min-confidence", type=int, metavar="N")
        flt.add_argument("--max-confidence", type=int, metavar="N")
        flt.add_argument("--review-status", type=str.upper, metavar="STATUS")
        flt.add_argument("--share-level", type=str.upper, metavar="LEVEL")
        flt.add_argument(
            "--include-expired", action="store_true", help="include expired descriptors"
        )
        flt.add_argument(
            "--sort-by",
            type=str.lower,
            choices=["relevance", "create_time"],
            help="ordering of results",
        )

        out = ap.add_argument_group("output")
        out.add_argument(
            "--columns",
            type=_columns,
            default=_DEFAULT_COLUMNS,
            metavar="COL,COL",
            help="default: %(default)s",
        )
        out.add_argument(
            "--list-columns", action="store_true", help="print available columns"
        )
        out.add_argument(
            "--format",
            choices=["csv", "jsonl"],
            default="csv",
            help="csv (default), or a JSON object per line",
        )
        out.add_argument("--output", "-o", metavar="FILE", help="default: stdout")
        out.add_argument(
            "--limit", type=int, metavar="N", help="stop after this many results"
        )
        out.add_argument(
            "--page-size",
            type=_page_size,
            default=_MAX_PAGE_SIZE,
            help="results per request (max %(default)s)",
        )

    def __init__(
        self,
        collabs: t.Sequence[str] = (),
        privacy_groups: t.Sequence[int] = (),
        text: t.Optional[str] = None,
        strict_text: bool = False,
        tags: t.Sequence[str] = (),
        tags_all: bool = False,
        status: t.Optional[str] = None,
        owners: t.Sequence[int] = (),
        indicator_type: t.Optional[str] = None,
        since: t.Optional[int] = None,
        until: t.Optional[int] = None,
        min_confidence: t.Optional[int] = None,
        max_confidence: t.Optional[int] = None,
        review_status: t.Optional[str] = None,
        share_level: t.Optional[str] = None,
        include_expired: bool = False,
        sort_by: t.Optional[str] = None,
        columns: t.Sequence[str] = tuple(_DEFAULT_COLUMNS),
        list_columns: bool = False,
        format: str = "csv",
        output: t.Optional[str] = None,
        limit: t.Optional[int] = None,
        page_size: int = _MAX_PAGE_SIZE,
    ) -> None:
        self.collabs = list(collabs)
        self.privacy_groups = list(privacy_groups)
        self.text = text
        self.strict_text = strict_text
        self.tags = list(tags)
        self.tags_all = tags_all
        self.status = status
        self.owners = list(owners)
        self.indicator_type = indicator_type
        self.since = since
        self.until = until
        self.min_confidence = min_confidence
        self.max_confidence = max_confidence
        self.review_status = review_status
        self.share_level = share_level
        self.include_expired = include_expired
        self.sort_by = sort_by.upper() if sort_by else None
        self.columns = list(columns)
        self.list_columns = list_columns
        self.format = format
        self.output = output
        self.limit = limit
        self.page_size = page_size

    def get_te_api(self) -> ThreatExchangeAPI:
        creds = FBThreatExchangeCredentials.get(FBThreatExchangeSignalExchangeAPI)
        return ThreatExchangeAPI(creds.api_token)

    def _resolve_privacy_groups(self, settings: CLISettings) -> t.List[int]:
        groups = list(self.privacy_groups)
        for name in self.collabs:
            collab = settings.get_collab(name)
            if collab is None:
                raise CommandError.user(f"No such collab '{name}'")
            if not isinstance(collab, FBThreatExchangeCollabConfig):
                raise CommandError.user(
                    f"Collab '{name}' is a {collab.api} collab. "
                    "`query` only works with fb_threatexchange"
                )
            groups.append(collab.privacy_group)
        return list(dict.fromkeys(groups))  # Dedupe, keep order

    def execute(self, settings: CLISettings) -> None:
        if self.list_columns:
            for name, (field, _) in _COLUMNS.items():
                print(f"{name:14} (API field: {field})")
            return
        if self.tags_all and not self.tags:
            raise CommandError.user("--tags-all requires --tags")
        if self.strict_text and not self.text:
            raise CommandError.user("--strict-text requires --text")
        if self.limit is not None and self.limit < 1:
            raise CommandError.user("--limit must be at least 1")

        groups = self._resolve_privacy_groups(settings)
        fields = list(dict.fromkeys(_COLUMNS[c][0] for c in self.columns))
        cursor = self.get_te_api().search_threat_descriptors(
            privacy_groups=groups,
            text=self.text,
            strict_text=True if self.strict_text else None,
            tags=self.tags,
            tags_are_anded=True if self.tags_all else None,
            status=self.status,
            owners=self.owners,
            type=self.indicator_type,
            since=self.since,
            until=self.until,
            min_confidence=self.min_confidence,
            max_confidence=self.max_confidence,
            review_status=self.review_status,
            share_level=self.share_level,
            sort_by=self.sort_by,
            include_expired=True if self.include_expired else None,
            # No point asking for 1000 if we'll only keep a few
            page_size=min(self.page_size, self.limit or self.page_size),
            fields=fields,
        )

        try:
            if self.output:
                with open(self.output, "w", newline="", encoding="utf-8") as f:
                    count = self._write(cursor, f)
            else:
                count = self._write(cursor, sys.stdout)
        except BrokenPipeError:
            return  # Reader (e.g. `head`) went away
        except requests.HTTPError as e:
            raise CommandError.external_dependency(_describe_http_error(e)) from e
        except requests.RequestException as e:
            raise CommandError.external_dependency(f"Request failed: {e}") from e
        if sys.stderr.isatty():
            self.stderr("\r\x1b[K", end="")  # Clear the progress line
        self.stderr(f"Wrote {count} results")

    def _write(self, cursor: t.Iterable[t.List[t.Any]], out: t.TextIO) -> int:
        readers = [_COLUMNS[c][1] for c in self.columns]
        writer = csv.writer(out) if self.format == "csv" else None
        if writer:
            writer.writerow(self.columns)
        count = 0
        for page in cursor:
            for descriptor in page:
                values = [read(descriptor) for read in readers]
                if writer:
                    writer.writerow(
                        " ".join(v) if isinstance(v, list) else v for v in values
                    )
                else:
                    out.write(json.dumps(dict(zip(self.columns, values))) + "\n")
                count += 1
                if self.limit is not None and count >= self.limit:
                    return count  # Don't fetch another page
            if sys.stderr.isatty():
                self.stderr(f"...{count} so far", end="\r")
        return count


def _describe_http_error(e: requests.HTTPError) -> str:
    """The Graph API says what was wrong with the request in the body"""
    try:
        error = e.response.json()["error"]
        return f"ThreatExchange API error {error.get('code')}: {error.get('message')}"
    except (ValueError, KeyError, TypeError, AttributeError):
        return f"ThreatExchange API request failed: {e}"
