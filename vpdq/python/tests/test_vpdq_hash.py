# Copyright (c) Meta Platforms, Inc. and affiliates.
import vpdq  # type: ignore
import pytest
import test_util
from pathlib import Path
import glob
import re
from typing import Union, Sequence, NamedTuple
from collections import namedtuple
import json

DIR = Path(__file__).parent
VPDQ_DIR = DIR.parent.parent
SAMPLE_HASH_FOLDER = VPDQ_DIR / "sample-hashes"
SAMPLE_VIDEOS = VPDQ_DIR.parent / Path("tmk/sample-videos")
DISTANCE_TOLERANCE = 31
QUALITY_TOLERANCE = 50

PROJECT_DIR = Path(__file__).parents[3]
HASH_FOLDER = PROJECT_DIR / SAMPLE_HASH_FOLDER
VIDEO_FOLDER = PROJECT_DIR / SAMPLE_VIDEOS
test_hashes = {}
sample_hashes = {}


def get_test_file_paths() -> Sequence[Path]:
    test_files = []
    for fileStr in glob.iglob(f"{VIDEO_FOLDER}/**/*.mp4", recursive=True):
        file = Path(fileStr)
        if not (VIDEO_FOLDER / f"{file.name}").is_file():
            print(f"Video file {file.name} doesn't exist. Skipping.")
            continue
        test_files.append(file)
    assert len(test_files) > 0
    return test_files


def test_vpdq_utils():
    test_files = get_test_file_paths()
    sample = Path(f"{HASH_FOLDER}/{test_files[0].stem}.txt")
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
    test_files = get_test_file_paths()
    video_file = Path(f"{VIDEO_FOLDER}/{test_files[0].name}")
    with pytest.raises(ValueError, match="Seconds_per_hash must be non-negative"):
        vpdq.computeHash(input_video_filename=video_file, seconds_per_hash=-1)

    with pytest.raises(ValueError, match="Downsample_width must be non-negative"):
        vpdq.computeHash(input_video_filename=video_file, downsample_width=-1)

    with pytest.raises(ValueError, match="Downsample_height must be non-negative"):
        vpdq.computeHash(input_video_filename=video_file, downsample_height=-1)

    with pytest.raises(ValueError, match="Input_video_filename doesn't exist"):
        vpdq.computeHash(input_video_filename="nonexisting")


def get_downsampled_hash_files(
    input_hash_file_path: Union[Path, str]
) -> Sequence[NamedTuple]:
    """
    Get all the downsampled hash files that match the input hash file name
    The input hash file name should be in the format of <base_name>.txt
    The downsampled hash file name should be in the format of <base_name>-<width>x<height>.txt
    """

    # Define the regular expression pattern to match the desired filenames
    pattern = r"(.*)-(\d+)x(\d+)\.txt"

    # Get the base file name without resolution and extension
    base_file_name_match = re.match(r"(.*)(?=\.txt)", Path(input_hash_file_path).name)
    if base_file_name_match is not None:
        base_file_name = base_file_name_match.group(1)
    else:
        return []

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
    test_files = get_test_file_paths()

    for file in test_files:
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


def test_to_dict_serialize_from_dict_deserialize():
    # Get a list of all sample files
    test_files = get_test_file_paths()

    for test_file in test_files:
        sample_file = Path(HASH_FOLDER) / f"{test_file.stem}.txt"
        assert sample_file.is_file()

        for sample_instance in test_util.read_file_to_hash(sample_file):
            # Test the to_dict method
            serialized_dict = sample_instance.to_dict()
            assert serialized_dict == {
                "quality": sample_instance.quality,
                "frame_number": sample_instance.frame_number,
                "hash": vpdq.hash_to_hex(sample_instance.hash),
                "timestamp": sample_instance.timestamp,
            }

            # Test the serialize method
            serialized_str = sample_instance.serialize()
            expected_json = json.dumps(serialized_dict)
            assert serialized_str == expected_json

            # Test the from_dict method
            deserialized_instance = vpdq.VpdqFeature.from_dict(serialized_dict)
            assert deserialized_instance.quality == sample_instance.quality
            assert deserialized_instance.frame_number == sample_instance.frame_number
            assert deserialized_instance.hash == sample_instance.hash
            assert deserialized_instance.timestamp == sample_instance.timestamp

            # Test the deserialize method
            deserialized_from_json = vpdq.VpdqFeature.deserialize(expected_json)
            assert deserialized_from_json.quality == sample_instance.quality
            assert deserialized_from_json.frame_number == sample_instance.frame_number
            assert deserialized_from_json.hash == sample_instance.hash
            assert deserialized_from_json.timestamp == sample_instance.timestamp
