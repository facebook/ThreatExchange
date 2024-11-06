# Copyright (c) Meta Platforms, Inc. and affiliates.

import pathlib
import tempfile
import os
from threatexchange.cli.tests.e2e_test_helper import (
    ThreatExchangeCLIE2eHelper,
    ThreatExchangeCLIE2eTest,
)
from threatexchange.content_type.content_base import RotationType
from threatexchange.content_type.photo import PhotoContent
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

    def test_non_photo_match_with_rotations(self):
        with tempfile.NamedTemporaryFile() as f:
            for content_type in ["url", "text", "video"]:
                self.assert_cli_usage_error(
                    ("--rotations", content_type, f.name),
                    msg_regex="--rotations flag is only available for Photo content type",
                )

    def test_photo_hash_with_rotations(self):
        test_file = pathlib.Path(
            __file__ + "../../../../../../pdq/data/bridge-mods/aaa-orig.jpg"
        ).resolve()

        hash_cmd = ThreatExchangeCLIE2eHelper()
        hash_cmd.COMMON_CALL_ARGS = ("hash",)
        hash_cmd._state_dir = pathlib.Path()

        rotated_images = PhotoContent.all_simple_rotations(test_file.read_bytes())

        for rotation, image in rotated_images.items():
            with tempfile.NamedTemporaryFile() as tmp_file:
                tmp_file.write(image)

                if rotation == RotationType.ROTATE270:
                    rotation = RotationType.ROTATE90
                elif rotation == RotationType.ROTATE90:
                    rotation = RotationType.ROTATE270

                self.assert_cli_output(
                    ("--rotations", "photo", tmp_file.name),
                    f"pdq {rotation.name} 16 (Sample Signals) INVESTIGATION_SEED",
                )
