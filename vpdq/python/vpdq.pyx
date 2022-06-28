# distutils: language = c++
# cython: language_level=3
import numpy as np
cimport numpy as np
import cv2

from dataclasses import dataclass
from libcpp cimport bool
from libcpp.vector cimport vector
from libcpp.string cimport string
from vpdq_util import hash_to_hex


cdef extern from "pdq/cpp/common/pdqhashtypes.h" namespace "facebook::pdq::hashing":
    cdef struct Hash256:
        unsigned short w[16];
    int hammingDistance(
        Hash256 hash1,
        Hash256 hash2
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

cdef extern from "vpdq/cpp/hashing/filehasher.h" namespace "facebook::vpdq::hashing":
    bool hashVideoFile(
        string input_video_filename,
        vector[vpdqFeature]& pdqHashes,
        string ffmpeg_path,
        bool verbose,
        int seconds_per_hash,
        int width,
        int height,
        const char* argv0
    )

@dataclass
class vpdq_feature:
    quality: int
    frame_number: int
    hash: Hash256
    hex: str
    def __init__(self, quality, frame_number, hash):
        self.quality = quality
        self.frame_number = frame_number
        self.hash = hash
        self.hex = hash_to_hex(hash)
    def hamming_distance(self, that):
        return hammingDistance(self.hash, that.hash)

def fromString(str_hash):
    return fromStringOrDie(str(str_hash).encode('utf-8'))

def hamming_distance(hash1, hash2):
    """Return the hamming distance between two pdq hashes

    Args:
        hash1 (Hash256)
        hash2 (Hash256)

    Returns:
        int: The hamming distance
    """
    return hammingDistance(hash1, hash2)

def computeHash(input_video_filename, ffmpeg_path, verbose, seconds_per_hash, width, height):
    """Compute vpdq hash

    Args:
        input_video_filename (str): Input video file path
        ffmpeg_path (str): ffmpeg path
        verbose (bool): If verbose, will print detailed information
        seconds_per_hash (int): The frequence(per second) a hash is generated from the video
        width (int): Width to downsample the video to before hashing frames.. If it is 0, will use the original width of the video to hash
        height (int): Height to downsample the video to before hashing frames.. If it is 0, will use the original height of the video to hash
    Returns:
        list of vpdq_feature: VPDQ hash from the video
    """
    cdef vector[vpdqFeature] vpdq_hash;
    if width == 0:
        vid = cv2.VideoCapture(input_video_filename)
        width = vid.get(cv2.CAP_PROP_FRAME_WIDTH)

    if height == 0:
        vid = cv2.VideoCapture(input_video_filename)
        height = vid.get(cv2.CAP_PROP_FRAME_HEIGHT)

    rt = hashVideoFile(
        input_video_filename.encode('utf-8'),
        vpdq_hash,
        ffmpeg_path.encode('utf-8'),
        verbose,
        seconds_per_hash,
        width,
        height,
        "vpdqPY"
        )

    hashs= [vpdq_feature(hash.quality,
                         hash.frameNumber,
                         hash.pdqHash)  for hash in vpdq_hash]
    return hashs
