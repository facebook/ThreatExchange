# Copyright (c) Meta Platforms, Inc. and affiliates.
import vpdq
import pytest
import test_util
import os
from pathlib import Path
import glob
import re
from typing import Union
from collections import namedtuple

DIR = Path(__file__).parent
VPDQ_DIR = DIR.parent.parent
SAMPLE_HASH_FOLDER = VPDQ_DIR / "sample-hashes"
SAMPLE_VIDEOS = VPDQ_DIR.parent / Path("tmk/sample-videos")
DISTANCE_TOLERANCE = 31
QUALITY_TOLERANCE = 50
TEST_FILES = [
    "chair-19-sd-bar",
    "chair-20-sd-bar",
    "chair-22-sd-grey-bar",
    "chair-22-sd-sepia-bar",
    "chair-22-with-large-logo-bar",
    "chair-22-with-small-logo-bar",
    "chair-orig-22-fhd-no-bar",
    "chair-orig-22-hd-no-bar",
    "chair-orig-22-sd-bar",
    "doorknob-hd-no-bar",
    "pattern-hd-no-bar",
    "pattern-longer-no-bar",
    "pattern-sd-grey-bar",
    "pattern-sd-with-large-logo-bar",
    "pattern-sd-with-small-logo-bar",
]

PROJECT_DIR = Path(__file__).parents[3]
HASH_FOLDER = PROJECT_DIR / SAMPLE_HASH_FOLDER
VIDEO_FOLDER = PROJECT_DIR / SAMPLE_VIDEOS
test_hashes = {}
sample_hashes = {}

TEST_FILES = []
for fileStr in glob.iglob(f"{VIDEO_FOLDER}/**/*.mp4", recursive=True):
    file = Path(fileStr)
    if not (VIDEO_FOLDER / f"{file.name}").is_file():
        print(f"Video file {file.name} doesn't exist. Skipping.")
        continue
    TEST_FILES.append(file)
assert len(TEST_FILES) > 0


def test_vpdq_utils():
    sample = Path(f"{HASH_FOLDER}/{TEST_FILES[0].stem}.txt")
    assert sample.is_file()
    ret = test_util.read_file_to_hash(sample)
    with open(sample, "r") as file:
        lines = file.readlines()
    for line, feature in zip(lines, ret):
        line = line.strip()
        content = line.split(",")
        hex_hash = content[2]
        assert vpdq.str_to_hash(hex_hash) == feature.hash
        assert vpdq.hash_to_hex(feature.hash) == hex_hash


def test_error_checking():
    video_file = Path(f"{VIDEO_FOLDER}/{TEST_FILES[0].name}")
    with pytest.raises(ValueError, match="Seconds_per_hash must be non-negative"):
        vpdq.computeHash(input_video_filename=video_file, seconds_per_hash=-1)

    with pytest.raises(ValueError, match="Downsample_width must be non-negative"):
        vpdq.computeHash(input_video_filename=video_file, downsample_width=-1)

    with pytest.raises(ValueError, match="Downsample_height must be non-negative"):
        vpdq.computeHash(input_video_filename=video_file, downsample_height=-1)

    with pytest.raises(ValueError, match="Input_video_filename doesn't exist"):
        vpdq.computeHash(input_video_filename="nonexisting")


def get_downsampled_hash_files(input_hash_file_path: Union[Path, str]):
    # Define the regular expression pattern to match the desired filenames
    pattern = r"(.*)-(\d+)x(\d+)\.txt"

    # Get the base file name without resolution and extension
    base_file_name = re.match(r"(.*)(?=\.txt)", input_hash_file_path.name).group(1)

    pathanddim = namedtuple("pathanddim", ["path", "width", "height"])

    all_matches = []
    for fileStr in HASH_FOLDER.iterdir():
        file = Path(fileStr)
        if file.is_file():
            matches = re.findall(pattern, file.name)
            for match in matches:
                name = match[0]
                width = match[1]
                height = match[2]
                # Only print matches that have the same base name as the input file
                if name == base_file_name:
                    new_match = pathanddim(Path(file), width, height)
                    all_matches.append(new_match)
    return all_matches


def test_compare_hashes():
    """This regression test is creating hashes from sample videos and compare them with the provided hashes line by line.
    Two VPDQ features are considered the same if each line of the hashes are within DISTANCE_TOLERANCE.
    For hashes that have a quality lower than QUALITY_TOLERANCE, the test will skip them for comparing.
    """

    for file in TEST_FILES:
        # Load the hash file truth
        hash_file = Path(f"{HASH_FOLDER}/{file.stem}.txt")
        assert hash_file.is_file()
        ret = test_util.read_file_to_hash(hash_file)
        assert ret is not None
        sample_hashes[file] = ret

        # Calculate the hash of file
        assert file.is_file()
        ret = vpdq.computeHash(input_video_filename=file, seconds_per_hash=0)
        assert ret is not None
        test_hashes[file] = ret

        print("Comparing hash for video:", file)
        hash1 = test_hashes[file]
        hash2 = sample_hashes[file]
        assert len(hash1) == len(hash2)
        for h1, h2 in zip(hash1, hash2):
            if h1.quality >= QUALITY_TOLERANCE and h2.quality >= QUALITY_TOLERANCE:
                assert h1.hamming_distance(h2) < DISTANCE_TOLERANCE
                assert h1.frame_number == h2.frame_number

        # Compare the downsampled hashes
        for downsampled_hash_file_pathanddim in get_downsampled_hash_files(hash_file):
            downsampled_hash_file = downsampled_hash_file_pathanddim.path
            downsampled_width = int(downsampled_hash_file_pathanddim.width)
            downsampled_height = int(downsampled_hash_file_pathanddim.height)

            # Load the downsampled hash file truth
            assert downsampled_hash_file.is_file()
            ret = test_util.read_file_to_hash(downsampled_hash_file)
            assert ret is not None
            sample_hashes[downsampled_hash_file] = ret

            # Calculated downsampled hash of test file
            assert file.is_file()
            ret = vpdq.computeHash(
                input_video_filename=file,
                seconds_per_hash=0,
                downsample_width=downsampled_width,
                downsample_height=downsampled_height,
            )
            assert ret is not None
            test_hashes[downsampled_hash_file] = ret

            print("Comparing hash for downsampled video:", downsampled_hash_file)
            hash1 = test_hashes[downsampled_hash_file]
            hash2 = sample_hashes[downsampled_hash_file]
            assert len(hash1) == len(hash2)
            for h1, h2 in zip(hash1, hash2):
                if h1.quality >= QUALITY_TOLERANCE and h2.quality >= QUALITY_TOLERANCE:
                    assert h1.hamming_distance(h2) < DISTANCE_TOLERANCE
                    assert h1.frame_number == h2.frame_number


@pytest.mark.skipif(
    os.getenv("GENERATE_HASHES") != "1", reason="Skip generating new hashes."
)
def test_generate_hashes():
    """
    This test is to generate hashes for the sample videos.
    The hashes will be saved in the same folder as SAMPLE_HASH_FOLDER.
    Hashes are generated

    If env OVERWRITE_HASHES is set, it will overwrite existing hashes in the folder.
    This can be used to update the hashes for the sample videos if vpdq is changed.
    """

    overwrite = os.getenv("OVERWRITE_HASHES") == "1"
    print(f"Generating hashes. Overwriting existing hashes: {overwrite}")
    test_util.generate_hashes(SAMPLE_HASH_FOLDER, TEST_FILES, overwrite=overwrite)

    # Generate 128x128 downsampled hashes for the sample videos
    test_util.generate_hashes(
        SAMPLE_HASH_FOLDER,
        TEST_FILES,
        overwrite=overwrite,
        downsample_width=128,
        downsample_height=128,
    )
