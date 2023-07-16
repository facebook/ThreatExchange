# Copyright (c) Meta Platforms, Inc. and affiliates.
import vpdq
import typing as t
from pathlib import Path
from typing import List, Union


def read_file_to_hash(input_hash_filename: str) -> t.List[vpdq.VpdqFeature]:
    """Read hash file and return vpdq hash

    Args:
        input_hash_filename (str): Input hash file path

    Returns:
        list of VpdqFeature: vpdq hash from the hash file"""

    hash = []
    with open(input_hash_filename, "r") as file:
        lines = file.readlines()
    for line in lines:
        line = line.strip()
        content = line.split(",")
        pdq_hash = vpdq.str_to_hash(content[2])
        feature = vpdq.VpdqFeature(
            int(content[1]), int(content[0]), pdq_hash, float(content[3])
        )
        hash.append(feature)

    return hash


def generate_hashes(
    output_folder: Union[Path, str],
    input_filepaths: List[Union[Path, str]],
    overwrite: bool = False,
    downsample_width: int = 0,
    downsample_height: int = 0,
) -> None:
    """
    Generate vpdq hashes for the test videos
    and write them to files in output_folder

    If overwrite is set, it will overwrite existing hashes in the folder.
    """
    output_folder = Path(output_folder)
    if not output_folder.exists():
        print(f"Creating output directory at {output_folder}")
        output_folder.mkdir(parents=True, exist_ok=True)

    for fileStr in input_filepaths:
        file = Path(fileStr)
        if downsample_width > 0 and downsample_height > 0:
            output_hash_filename = (
                output_folder
                / f"{file.stem}-{downsample_width}x{downsample_height}.txt"
            )
        else:
            output_hash_filename = output_folder / f"{file.stem}.txt"

        if not overwrite and output_hash_filename.exists():
            print(f"Hash file {output_hash_filename.name} already exists. Skipping.")
            continue

        vpdq_hash = vpdq.computeHash(
            input_video_filename=file,
            seconds_per_hash=0,
            downsample_width=downsample_width,
            downsample_height=downsample_height,
        )

        with open(output_hash_filename, "w") as output_file:
            for feature in vpdq_hash:
                output_file.write(
                    f"{feature.frame_number},{feature.quality},{vpdq.hash_to_hex(feature.hash)},{feature.timestamp:.3f}\n"
                )
