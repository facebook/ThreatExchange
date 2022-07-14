# distutils: language = c++
# cython: language_level=3
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
import numpy as np
cimport numpy as np
import cv2
import typing as t

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
        float timeStamp;


cdef extern from "vpdq/cpp/hashing/filehasher.h" namespace "facebook::vpdq::hashing":
    bool hashVideoFile(
        string input_video_filename,
        vector[vpdqFeature]& pdqHashes,
        string ffmpeg_path,
        bool verbose,
        double seconds_per_hash,
        int width,
        int height,
        double frames_per_sec,
        const char* argv0
    )

@dataclass
class VpdqFeature:
    quality: int
    frame_number: int
    hash: Hash256
    hex: str
    timestamp: double

    def __init__(
        self, quality: int, frame_number: int, hash: "Hash256", timestamp: double
    ):
        self.quality = quality
        self.frame_number = frame_number
        self.hash = hash
        self.hex = hash_to_hex(hash)
        self.timestamp = timestamp

    def hamming_distance(self, that: "vpdq_feature"):
        return hammingDistance(self.hash, that.hash)


def hash_to_hex(hash_value: "Hash256"):
    """Convect from pdq hash to hex str

    Args:
        hash_value

    Returns:
        str: hex str of hash
    """
    return hashToString(hash_value)


def str_to_hash(str_hash: str):
    return fromStringOrDie(str(str_hash).encode("utf-8"))


def hamming_distance(hash1: "Hash256", hash2: "Hash256"):
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
    input_video_filename: str,
    ffmpeg_path: str = "ffmpeg",
    seconds_per_hash: double = 0,
    verbose: bool = False,
    downsample_width: int = 0,
    downsample_height: int = 0,
):
    """Compute vpdq hash

    Args:
        input_video_filename: Input video file path
        ffmpeg_path: ffmpeg path
        verbose: If verbose, will print detailed information
        seconds_per_hash: The frequence(per second) a hash is generated from the video. If it is 0, will generate every frame's hash
        downsample_width: Width to downsample the video to before hashing frames.. If it is 0, will use the original width of the video to hash
        downsample_height: Height to downsample the video to before hashing frames.. If it is 0, will use the original height of the video to hash
    Returns:
        list of vpdq_feature: VPDQ hash from the video
    """
    cdef vector[vpdqFeature] vpdq_hash;
    vid = cv2.VideoCapture(input_video_filename)
    frames_per_sec = vid.get(cv2.CAP_PROP_FPS)
    if downsample_width == 0:
        downsample_width = vid.get(cv2.CAP_PROP_FRAME_WIDTH)

    if downsample_height == 0:
        downsample_height = vid.get(cv2.CAP_PROP_FRAME_HEIGHT)

    rt = hashVideoFile(
        input_video_filename.encode("utf-8"),
        vpdq_hash,
        ffmpeg_path.encode("utf-8"),
        verbose,
        seconds_per_hash,
        downsample_width,
        downsample_height,
        frames_per_sec,
        "vpdqPY",
    )
    if not rt:
        raise Exception("Fail to create VPDQ hash")

    hashes = [
        VpdqFeature(hash.quality, hash.frameNumber, hash.pdqHash, hash.timeStamp)
        for hash in vpdq_hash
    ]
    return hashes
