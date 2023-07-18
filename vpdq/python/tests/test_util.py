# Copyright (c) Meta Platforms, Inc. and affiliates.
import vpdq  # type: ignore
import typing as t


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
