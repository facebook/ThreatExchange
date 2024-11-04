import unittest
from unittest.mock import patch, MagicMock
import pathlib

from threatexchange.cli.hash_cmd import HashCommand
from threatexchange.cli.cli_config import CLISettings
from threatexchange.cli.exceptions import CommandError
from threatexchange.content_type.photo import PhotoContent, RotationType
from threatexchange.content_type.text import TextContent
from threatexchange.content_type.url import URLContent
from threatexchange.content_type.video import VideoContent


class TestHashCommand(unittest.TestCase):
    def setUp(self):
        self.settings = MagicMock(spec=CLISettings)
        self.test_file = pathlib.Path("threatexchange/tests/hashing/resources/LA.png")

    def test_rotations_with_non_photo_content(self):
        """Test that rotation flag raises error with non-photo content"""
        for content_type in [URLContent, TextContent, VideoContent]:
            command = HashCommand(
                content_type=content_type,
                signal_type=None,
                files=[self.test_file],
                rotations=True,
            )
            with self.assertRaises(CommandError) as context:
                command.execute(self.settings)
            self.assertIn(
                "--rotations flag is only available for Photo content type",
                str(context.exception),
            )

    def test_rotations_with_photo_content(self):
        """Test that photo rotations are properly processed"""
        command = HashCommand(
            content_type=PhotoContent,
            signal_type=None,
            files=[self.test_file],
            rotations=True,
        )

        with patch("builtins.print") as mock_print:
            command.execute(self.settings)
            self.assertEqual(mock_print.call_count, len(RotationType))

            for call in mock_print.call_args_list:
                print(call)
