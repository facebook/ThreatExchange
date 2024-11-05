# Copyright (c) Meta Platforms, Inc. and affiliates.

import pathlib
import tempfile
from threatexchange.cli.tests.e2e_test_helper import ThreatExchangeCLIE2eHelper, ThreatExchangeCLIE2eTest
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
        test_file = pathlib.Path("threatexchange/tests/hashing/resources/rgb.jpeg")

        hash_cmd = ThreatExchangeCLIE2eHelper()
        hash_cmd.COMMON_CALL_ARGS = ("hash",)
        hash_cmd._state_dir = pathlib.Path()

        hash = hash_cmd.cli_call("photo", str(test_file))
        assert hash == "pdq fb4eed46cb8a6c78819ca06b756c541f7b07ef6d02c82fccd00f862166272cda\n"

        # rotated_images = PhotoContent.all_simple_rotations(test_file.read_bytes())

        # img = rotated_images[RotationType.ROTATE90] #try with 1 rotated image first

        # with tempfile.NamedTemporaryFile() as tmp_file:
        #     img = rotated_images[RotationType.ROTATE90]
        #     tmp_file.write(img)
        #     self.assert_cli_output(
        #         ("--rotations", "photo", "--", tmp_file.name),
        #         "video_md5 - (Sample Signals) INVESTIGATION_SEED",
        #     )
