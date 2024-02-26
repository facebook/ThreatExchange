# distutils: language = c++
# cython: language_level=3
# Copyright (c) Meta Platforms, Inc. and affiliates.
import typing as t
import json

from pathlib import Path
from dataclasses import dataclass
from libcpp cimport bool
from libcpp.vector cimport vector
from libcpp.string cimport string


cdef extern from "pdq/cpp/common/pdqhashtypes.h" namespace "facebook::pdq::hashing":
    cdef struct Hash256:
        unsigned short w[16];
    int hammingDistance(
        Hash256 hash1,
        Hash256 hash2
    )
    string hashToString(
        Hash256 hash
    )

cdef extern from "pdq/cpp/common/pdqhashtypes.h" namespace "facebook::pdq::hashing::Hash256":
    Hash256 fromStringOrDie(
        char* hex_str
    )

cdef extern from "vpdq/cpp/hashing/vpdqHashType.h" namespace "facebook::vpdq::hashing":
    cdef struct vpdqFeature:
        Hash256 pdqHash;
        int frameNumber;
        int quality;
        double timeStamp;


cdef extern from "vpdq/cpp/hashing/filehasher.h" namespace "facebook::vpdq::hashing":
    bool hashVideoFile(
        string input_video_filename,
        vector[vpdqFeature]& pdqHashes,
        bool verbose,
        double seconds_per_hash,
        int width,
        int height,
        unsigned int thread_count,
    )


@dataclass
class VpdqFeature:
    quality: int
    frame_number: int
    hash: Hash256
    hex: str
    timestamp: float

    def __init__(
        self, quality: int, frame_number: int, hash: Hash256, timestamp: float
    ):
        self.quality = quality
        self.frame_number = frame_number
        self.hash = hash
        self.hex = hash_to_hex(hash)
        self.timestamp = timestamp

    def hamming_distance(self, that: VpdqFeature):
        return hammingDistance(self.hash, that.hash)
    
    def to_dict(self) -> dict:
        """Serialize VpdqFeature instance to a dictionary."""
        return {
            'quality': self.quality,
            'frame_number': self.frame_number,
            'hash': hash_to_hex(self.hash),
            'timestamp': self.timestamp,
        }

    def serialize(self) -> str:
        """Serialize VpdqFeature instance to a JSON-formatted string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> VpdqFeature:
        """Create VpdqFeature instance from a dictionary."""
        return cls(
            quality=data['quality'],
            frame_number=data['frame_number'],
            hash=str_to_hash(data['hash']),
            timestamp=data['timestamp'],
        )

    @classmethod
    def deserialize(cls, serialized: str) -> VpdqFeature:
        """Create VpdqFeature instance from a JSON-formatted string."""
        data = json.loads(serialized)
        return cls.from_dict(data)


def hash_to_hex(hash_value: Hash256) -> str:
    """Convert from pdq hash to hex str

    Args:
        hash_value

    Returns:
        str: hex str of hash
    """
    return str(hashToString(hash_value), "utf-8")


def str_to_hash(str_hash: str):
    return fromStringOrDie(str(str_hash).encode("utf-8"))


def hamming_distance(hash1: Hash256, hash2: Hash256) -> int:
    """
    Return the hamming distance between two pdq hashes

    Args:
        hash1
        hash2

    Returns:
        int: The hamming distance
    """
    return hammingDistance(hash1, hash2)


def computeHash(
    input_video_filename: t.Union[str, Path],
    ffmpeg_path: t.Union[str, None] = None,
    seconds_per_hash: float = 1.0,
    verbose: bool = False,
    downsample_width: int = 0,
    downsample_height: int = 0,
    thread_count: int = 0,
) -> t.List[VpdqFeature]:
    """Compute vpdq hash

    Args:
        input_video_filename: Input video file path
        ffmpeg_path: ffmpeg path (this is not used anymore)
        verbose: If verbose, will print detailed information
        seconds_per_hash: The frequence(per second) a hash is generated from the video. If it is 0, will generate every frame's hash
        downsample_width: Width to downsample the video to before hashing frames. If it is 0, will use the original width of the video to hash
        downsample_height: Height to downsample the video to before hashing frames. If it is 0, will use the original height of the video to hash
        thread_count: Number of threads for hashing. If it is 0, will use choose automatically
    Returns:
        list of vpdq_feature: VPDQ hash from the video
    """
    str_path = str(input_video_filename)
    if not Path(str_path).is_file():
        raise ValueError("Input_video_filename doesn't exist")
    if seconds_per_hash < 0:
        raise ValueError("Seconds_per_hash must be non-negative")
    if downsample_width < 0:
        raise ValueError("Downsample_width must be non-negative")
    if downsample_height < 0:
        raise ValueError("Downsample_height must be non-negative")
    if thread_count < 0:
        raise ValueError("Thread_count must be non-negative")
    cdef vector[vpdqFeature] vpdq_hash;
    

    rt = hashVideoFile(
        str_path.encode("utf-8"),
        vpdq_hash,
        verbose,
        seconds_per_hash,
        downsample_width,
        downsample_height,
        thread_count,
    )

    if not rt:
        raise Exception("Fail to create VPDQ hash")

    hashes = [
        VpdqFeature(hash.quality, hash.frameNumber, hash.pdqHash, hash.timeStamp)
        for hash in vpdq_hash
    ]
    return hashes


def _cli():
    import argparse

    ap = argparse.ArgumentParser(
        description="a simple wrapper for the vPDQ hashing algorithm"
    )
    ap.add_argument("file", help="the file to hash")
    ns = ap.parse_args()
    hashes = computeHash(ns.file)
    for hash in hashes:
        print(f"{hash.hex},{hash.quality},{hash.timestamp:.3f}")