# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import collections
import logging
import datetime
import logging
import time
import typing as t

from threatexchange.cli.cli_config import CLISettings
from threatexchange.cli.dataset_cmd import DatasetCommand
from threatexchange.exchanges.collab_config import CollaborationConfigBase
from threatexchange.exchanges.signal_exchange_api import (
    SignalExchangeAPI,
    TSignalExchangeAPICls,
)
from threatexchange.exchanges.fetch_state import (
    FetchCheckpointBase,
    FetchDeltaTyped,
    FetchedStateStoreBase,
)
from threatexchange.cli import command_base


class FetchCommand(command_base.Command):
    """
    Download content from signal exchange APIs to disk.

    Fetches data for collaborations that you've configured with
      $ threatexchange config collab edit

    Fetching is checkpointed, and you can safely interrupt by using CTRL+C.

    Some APIs require that you regularly re-fetch them within some number
    of days or else the stored data becomes invalid.

    This command is laconic by default, try `threatexchange -v fetch` for
    more granular details.
    """

    PROGRESS_PRINT_INTERVAL_SEC = 30

    @classmethod
    def init_argparse(cls, settings: CLISettings, ap) -> None:
        ap.add_argument(
            "--clear",
            action="store_true",
            help="delete fetched state and checkpoints "
            "(you almost never need to do this)",
        )
        ap.add_argument(
            "--skip-index-rebuild",
            action="store_true",
            help="don't rebuild indices after fetch",
        )
        ap.add_argument("--limit", type=int, help="stop after fetching this many items")
        ap.add_argument(
            "--time-limit-sec",
            type=int,
            metavar="SEC",
            help="stop fetching after this many seconds",
        )
        ap.add_argument(
            "--checkpoint-every",
            type=int,
            metavar="SEC",
            default=600,
            help="write state to disk if still fetching, or 0 to disable",
        )
        ap.add_argument(
            "--only-api",
            choices=[api.get_name() for api in settings.apis],
            help="only fetch from this API",
        )
        ap.add_argument(
            "--only-collab",
            metavar="NAME",
            help="only fetch for this collaboration",
        )

    def __init__(
        self,
        # Defaults to make it easier to call from match
        clear: bool = False,
        time_limit_sec: t.Optional[int] = None,
        limit: t.Optional[int] = None,
        skip_index_rebuild: bool = False,
        only_api: t.Optional[str] = None,
        only_collab: t.Optional[str] = None,
        checkpoint_every: int = 600,
    ) -> None:
        self.clear = clear
        self.time_limit_sec = time_limit_sec
        self.limit = limit
        self.skip_index_rebuild = skip_index_rebuild
        self.only_api = only_api
        self.only_collab = only_collab
        self.collabs: t.List[CollaborationConfigBase] = []

        # Limits
        self.total_fetched_count = 0
        self.start_time = time.time()
        self.last_checkpoint_time = time.time()
        self.checkpoint_every = checkpoint_every

        # Progress
        self.last_update_time: t.Optional[int] = None
        # Print first update after 5 seconds
        self.last_update_printed = time.time() - self.PROGRESS_PRINT_INTERVAL_SEC + 5
        self.progress_fetched_count = 0
        self.counts: t.Dict[str, int] = collections.Counter()

    def has_hit_limits(self):
        if self.limit is not None and self.total_fetched_count >= self.limit:
            return True
        if self.time_limit_sec is not None:
            if time.time() - self.start_time >= self.time_limit_sec:
                return True
        return False

    def should_checkpoint(self):
        if self.checkpoint_every <= 0:
            return False
        return time.time() > self.checkpoint_every + self.last_checkpoint_time

    def execute(self, settings: CLISettings) -> None:
        # Verify collab arguments
        self.collabs = settings.get_all_collabs()
        if self.only_collab:
            self.collabs = [c for c in self.collabs if c.name == self.only_collab]
            if not self.collabs:
                raise command_base.CommandError(
                    f"No such collab '{self.only_collab}'", 2
                )
        if all(not c.enabled for c in self.collabs):
            self.stderr("All collabs are disabled. Nothing to do.")
            return

        # Do work
        if self.clear:
            self.stderr("Clearing fetched state")
            for api in settings.apis:
                store = settings.fetched_state.get_for_api(api)
                for collab in self.collabs:
                    if self.only_collab not in (None, collab.name):
                        continue
                    logging.info("Clearing %s - %s", api.get_name(), collab.name)
                    store.clear(collab)
            return

        all_succeeded = True
        any_succeded = False

        for api in settings.apis:
            logging.info("Fetching all %s's configs", api.get_name())
            succeeded = self.execute_for_api(settings, api)
            all_succeeded &= succeeded
            any_succeded |= succeeded

        if any_succeded and not self.skip_index_rebuild:
            self.stderr("Rebuilding match indices...")
            DatasetCommand().execute_generate_indices(settings)

        if not all_succeeded:
            raise command_base.CommandError("Some collabs had errors!", 3)

    def execute_for_api(
        self, settings: CLISettings, api: TSignalExchangeAPICls
    ) -> bool:
        success = True
        for collab in self.collabs:
            if collab.api != api.get_name():
                continue
            if not collab.enabled:
                logging.debug(
                    "Skipping %s, disabled",
                )
                continue
            fetch_ok = self.execute_for_collab(settings, collab)
            success &= fetch_ok
        return success

    def execute_for_collab(
        self,
        settings: CLISettings,
        collab: CollaborationConfigBase,
    ) -> bool:
        api = settings.apis.get_instance_for_collab(collab)
        store = settings.fetched_state.get_for_api(api.__class__)
        checkpoint = self._verify_store_and_checkpoint(store, collab)

        self.progress_fetched_count = 0
        self.current_collab = collab.name
        self.current_api = api.get_name()
        completed = False

        try:
            it = api.fetch_iter(settings.get_all_signal_types(), checkpoint)
            delta: FetchDeltaTyped
            for delta in it:
                assert delta.checkpoint is not None  # Infinite loop protection
                progress_time = delta.checkpoint.get_progress_timestamp()
                logging.info(
                    "fetch() with %d new records%s",
                    len(delta.updates),
                    (
                        ""
                        if progress_time is None
                        else f" @ {_timeformat(progress_time)}"
                    ),
                )
                next_checkpoint = delta.checkpoint
                self._fetch_progress(len(delta.updates), next_checkpoint)
                if checkpoint is not None:
                    prev_time = checkpoint.get_progress_timestamp()
                    if prev_time is not None and progress_time is not None:
                        assert prev_time <= progress_time, (
                            "checkpoint time rewound? ",
                            "This can indicate a serious ",
                            "problem with the API and checkpointing",
                        )
                checkpoint = next_checkpoint  # Only used for the rewind check

                store.merge(collab, delta)
                if self.has_hit_limits():
                    self.stderr("Hit limits, checkpointing")
                    break
                if self.should_checkpoint():
                    self._print_progress(checkpoint=True)
                    store.flush()
                    self.last_checkpoint_time = time.time()
            completed = True
        except Exception:
            self._stderr_current("failed to fetch!")
            logging.exception("Failed to fetch %s", collab.name)
            return False
        except KeyboardInterrupt:
            self._stderr_current("Interrupted, writing a checkpoint...")
            raise
        finally:
            store.flush()

        self._print_progress(done=completed)
        return True

    def _verify_store_and_checkpoint(
        self, store: FetchedStateStoreBase, collab: CollaborationConfigBase
    ) -> t.Optional[FetchCheckpointBase]:
        checkpoint = store.get_checkpoint(collab)

        if checkpoint is not None and checkpoint.is_stale():
            logging.info("checkpoint stale for %s, clearing", collab.name)
            store.clear(collab)
            return None

        return checkpoint

    def _fetch_progress(self, batch_size: int, checkpoint: FetchCheckpointBase) -> None:
        self.progress_fetched_count += batch_size
        self.total_fetched_count += batch_size
        progress_ts = checkpoint.get_progress_timestamp()
        if progress_ts is not None:
            self.last_update_time = progress_ts

        now = time.time()
        if now - self.last_update_printed >= self.PROGRESS_PRINT_INTERVAL_SEC:
            self.last_update_printed = now
            self._print_progress()

    def _stderr_current(self, msg: str) -> None:
        assert self.current_api and self.current_collab
        self.stderr(
            f"[{self.current_api}] {self.current_collab} - {msg}",
        )

    def _print_progress(self, *, done=False, checkpoint=False):
        processed = "Fetching..."
        if done:
            processed = "Up to date"
        elif checkpoint:
            processed = "Checkpointing"
        elif self.progress_fetched_count:
            processed = f"Downloaded {self.progress_fetched_count} updates"

        from_time = ""
        if self.last_update_time is not None:
            if self.last_update_time <= 0:
                from_time = "ages long past"
            elif self.last_update_time >= time.time() - 1:
                from_time = "moments ago"
            else:
                from_time = _timeformat(self.last_update_time)
            from_time = f" at {from_time}"

        self._stderr_current(f"{processed}{from_time}")


def _timeformat(timestamp: int) -> str:
    return datetime.datetime.fromtimestamp(timestamp).isoformat()
