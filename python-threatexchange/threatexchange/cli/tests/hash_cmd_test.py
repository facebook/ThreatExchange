# Copyright (c) Meta Platforms, Inc. and affiliates.

import io
import pathlib
import tempfile
import pytest
from PIL import Image, ImageSequence
from threatexchange.cli.tests.e2e_test_helper import (
    ThreatExchangeCLIE2eHelper,
    te_cli,
)
from threatexchange.content_type.file import FileContent
from threatexchange.signal_type.pdq.pdq_hasher import pdq_from_bytes


@pytest.fixture
def hash_cli(
    te_cli: ThreatExchangeCLIE2eHelper,
) -> ThreatExchangeCLIE2eHelper:
    te_cli.COMMON_CALL_ARGS = ("hash",)
    return te_cli


@pytest.fixture
def tmp_file():
    with tempfile.NamedTemporaryFile() as f:
        yield pathlib.Path(f.name)


def test_file(hash_cli: ThreatExchangeCLIE2eHelper, tmp_file: pathlib.Path):
    tmp_file.write_text("http://evil.com")
    hash_cli.assert_cli_output(
        ("url", str(tmp_file)),
        "url_md5 6d3af727a4e7b025fd59a5469b3a9c57",
    )

    hash_cli.assert_cli_usage_error(("url", "blah.txt"))


def test_dashdash(hash_cli: ThreatExchangeCLIE2eHelper):
    hash_cli.assert_cli_output(
        ("url", "--", "http://evil.com"),
        "url_md5 6d3af727a4e7b025fd59a5469b3a9c57",
    )


def test_stdin(
    hash_cli: ThreatExchangeCLIE2eHelper,
    monkeypatch: pytest.MonkeyPatch,
    tmp_file: pathlib.Path,
):
    tmp_file.write_text("http://evil.com")

    with tmp_file.open() as fake_stin:
        monkeypatch.setattr("sys.stdin", fake_stin)
        hash_cli.assert_cli_output(
            ("url", "-"),
            "url_md5 6d3af727a4e7b025fd59a5469b3a9c57",
        )


def test_mixed(hash_cli: ThreatExchangeCLIE2eHelper, tmp_path: pathlib.Path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    a.write_text("http://evil.com", None)
    b.touch()

    hash_cli.assert_cli_output(
        ("url", str(a), str(b), "--", "fb.com"),
        [
            "url_md5 6d3af727a4e7b025fd59a5469b3a9c57",
            "url_md5 d41d8cd98f00b204e9800998ecf8427e",
            "url_md5 fb8191ebebc85f9eb6fd21e198f20979",
        ],
    )


def test_missing(hash_cli: ThreatExchangeCLIE2eHelper):
    hash_cli.assert_cli_usage_error(())
    hash_cli.assert_cli_usage_error(("photo",))


def test_rotations_with_non_photo_content(
    hash_cli: ThreatExchangeCLIE2eHelper, tmp_file: pathlib.Path
):
    """Test that rotation flag raises error with non-photo content"""
    for content_type in ["url", "text", "video"]:
        hash_cli.assert_cli_usage_error(
            ("--photo-preprocess=rotations", content_type, str(tmp_file)),
            msg_regex="--photo-preprocess flag is only available for Photo content type",
        )


def test_rotations_with_photo_content(hash_cli: ThreatExchangeCLIE2eHelper):
    """Test that photo rotations are properly processed"""
    resources_dir = (
        pathlib.Path(__file__).parent.parent.parent / "tests/hashing/resources"
    )
    test_file = resources_dir / "LA.png"

    hash_cli.assert_cli_output(
        ("--photo-preprocess=rotations", "photo", str(test_file)),
        [
            "ORIGINAL pdq accb6d39648035f8125c8ce6ba65007de7b54c67a2d93ef7b8f33b0611306715",
            "ROTATE90 pdq 1f70cbbc77edc5f9524faa1b18f3b76cd0a04a833e20f645d229d0acc8499c56",
            "ROTATE180 pdq 31ddf2513558de0ae56e4a8c8930cadde2ee084df3aed0a75fa512ea0e41e197",
            "ROTATE270 pdq c79931968e880f4b97196df4d5ea0fb489b99e2c10af0dceacf572809b815ea5",
            "FLIPX pdq aaca8605440c4a6735dbbf59b947df92e7bf161807e9cd88baf04579523098ab",
            "FLIPY pdq 559f78de2530abbdc663b131ed78f10072c4bb13f3acd6017d0e69150e413e5a",
            "FLIPPLUS1 pdq 86a860c1f2bd1a1ec65cf4d10ab55087b4b89f7857da59bbd9200fd5845cc3f9",
            "FLIPMINUS1 pdq 5bb15db9e8a1f03c174a380a55aeaa2985bde9c60abce301bde48df918b5c15b",
        ],
    )


def test_unletterbox_with_non_photo_content(
    hash_cli: ThreatExchangeCLIE2eHelper, tmp_file: pathlib.Path
):
    """Test that unletterbox flag raises error with non-photo content"""
    for content_type in ["url", "text", "video"]:
        hash_cli.assert_cli_usage_error(
            ("--photo-preprocess=unletterbox", content_type, str(tmp_file)),
            msg_regex="--photo-preprocess flag is only available for Photo content type",
        )


def test_unletterbox_with_photo_content(hash_cli: ThreatExchangeCLIE2eHelper):
    """Test that photo unletterboxing is properly processed"""
    resources_dir = (
        pathlib.Path(__file__).parent.parent.parent / "tests/hashing/resources"
    )
    test_file = resources_dir / "letterboxed_sample-b.jpg"
    clean_file = resources_dir / "sample-b.jpg"

    hash_cli.assert_cli_output(
        ("photo", str(clean_file)),
        [
            "pdq f8f8f0cee0f4a84f06370a22038f63f0b36e2ed596621e1d33e6b39c4e9c9b22",
        ],
    )

    """Test that photo unletterboxing is changed based on allowed threshold"""
    hash_cli.assert_cli_output(
        ("--photo-preprocess=unletterbox", "photo", str(test_file)),
        [
            "pdq d8f871cce0f4e84d8a370a32028f63f4b36e27d597621e1d33e6b39c4a9c9b22",
        ],
    )

    hash_cli.assert_cli_output(
        (
            "--photo-preprocess=unletterbox",
            "--black-threshold=25",
            "photo",
            str(test_file),
        ),
        [
            "pdq f8f8f0cee0f4a84f06370a22038f63f0b36e2ed596621e1d33e6b39c4e9c9b22",
        ],
    )


def test_file_content(hash_cli: ThreatExchangeCLIE2eHelper):
    """
    Test that FileContent correctly maps to PhotoContent or VideoContent
    and raises errors for unsupported file types.
    """
    resources_dir = (
        pathlib.Path(__file__).parent.parent.parent / "tests/hashing/resources"
    )
    # Paths for existing test images
    photo_jpg = resources_dir / "sample-b.jpg"
    photo_png = resources_dir / "LA.png"  # Replace with correct PNG file
    photo_jpeg_rgb = resources_dir / "rgb.jpeg"

    # JPEG Test Case
    hash_cli.assert_cli_output(
        ("file", str(photo_jpg)),
        [
            "pdq f8f8f0cee0f4a84f06370a22038f63f0b36e2ed596621e1d33e6b39c4e9c9b22",
        ],
    )

    # PNG Test Case
    hash_cli.assert_cli_output(
        ("file", str(photo_png)),
        [
            "pdq accb6d39648035f8125c8ce6ba65007de7b54c67a2d93ef7b8f33b0611306715",
        ],
    )

    # JPEG with RGB Profile Test Case
    hash_cli.assert_cli_output(
        ("file", str(photo_jpeg_rgb)),
        [
            "pdq fb4eed46cb8a6c78819ca06b756c541f7b07ef6d02c82fccd00f862166272cda",
        ],
    )

    # Create and test a temporary empty MP4 file (Video)
    with tempfile.NamedTemporaryFile(suffix=".mp4") as tmp_video_file:
        hash_cli.assert_cli_output(
            ("file", tmp_video_file.name),
            [
                "video_md5 d41d8cd98f00b204e9800998ecf8427e",
            ],
        )

    # Create and test a temporary empty AVI file (Video)
    with tempfile.NamedTemporaryFile(suffix=".avi") as tmp_avi_file:
        hash_cli.assert_cli_output(
            ("file", tmp_avi_file.name),
            [
                "video_md5 d41d8cd98f00b204e9800998ecf8427e",
            ],
        )

    # Create and test a temporary empty MOV file (Video)
    with tempfile.NamedTemporaryFile(suffix=".mov") as tmp_mov_file:
        hash_cli.assert_cli_output(
            ("file", tmp_mov_file.name),
            [
                "video_md5 d41d8cd98f00b204e9800998ecf8427e",
            ],
        )

    # Create and test a temporary static GIF file (1x1 pixel)
    with tempfile.NamedTemporaryFile(suffix=".gif") as tmp_static_gif:
        # Create a 100x100 multi-colored image
        static_img = Image.new("RGB", (100, 100))
        pixels = static_img.load()

        # Fill the image with colors to improve quality
        if pixels:
            for i in range(100):
                for j in range(100):
                    pixels[i, j] = ((i * 5) % 256, (j * 5) % 256, ((i + j) * 5) % 256)

        # Save the image as a static GIF
        static_img.save(tmp_static_gif.name, format="GIF")
        hash_cli.assert_cli_output(
            ("file", tmp_static_gif.name),
            [
                "pdq 77ffdd3a9405fbb0805027270fa7d7065e7cf8da0c0d795881002667e44f266f",
            ],
        )

    # Create and test a temporary animated GIF file (2 frames)
    with tempfile.NamedTemporaryFile(suffix=".gif") as tmp_animated_gif:
        animated_frames = [
            Image.new("RGB", (1, 1), color=(255, 0, 0)),  # Red frame
            Image.new("RGB", (1, 1), color=(0, 255, 0)),  # Green frame
        ]
        animated_frames[0].save(
            tmp_animated_gif.name,
            format="GIF",
            save_all=True,
            append_images=animated_frames[1:],
            duration=200,  # Frame duration
            loop=0,
        )
        hash_cli.assert_cli_output(
            ("file", tmp_animated_gif.name),
            [
                "video_md5 ec82a2d0d4d99a623ec2a939accc7de5",
            ],
        )

    # Create and test a temporary unsupported .txt file
    with tempfile.NamedTemporaryFile(suffix=".txt") as tmp_unsupported_file:
        tmp_unsupported_file.write(b"This is a test file.")  # Write dummy text
        tmp_unsupported_file.flush()
        # Assert that the CLI raises a CommandError for unsupported file type
        hash_cli.assert_cli_usage_error(
            ("file", tmp_unsupported_file.name),
            msg_regex="Unsupported file type: .txt",
        )
