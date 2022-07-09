# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
import vpdq


def read_file_to_hash(input_hash_filename: str) -> list[vpdq.VpdqFeature]:
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
            feature = vpdq.VpdqFeature(int(content[1]), int(content[0]), pdq_hash, float(content[3]))
            hash.append(feature)

    return hash


def output_hash_to_file(output_hash_filename, hashes):
    """Output vpdq hash to txt file

    Args:
        output_hash_filename (str): Output hash file path
        hash (list of VpdqFeature): Vpdq Hash"""

    with open(output_hash_filename, "w") as file:
        for cur in hashes:
            file.write(f"{cur.frame_number},{cur.quality},{hash_to_hex(cur.hash['w'])},{cur.timestamp:.3f}")
            file.write("\n")
