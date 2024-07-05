# Copyright (c) Meta Platforms, Inc. and affiliates.

import vpdq
import subprocess
import os
import argparse
from pathlib import Path
from contextlib import contextmanager
import time

VPDQ_MATCH_DIST = 31
DIR = Path(__file__).parents[2]
VIDEOS = DIR / "tmk/sample-videos"
OUTPUT = Path(__file__).parent / "hashes"
CPP_EXEC = Path(__file__).parents[1] / "cpp/build/apps/vpdq-hash-video"


@contextmanager
def timer(context: str, print_on_enter: bool = False):
    if print_on_enter:
        print(f"{context}...")
    start = time.perf_counter()
    end = start
    yield lambda: end - start
    end = time.perf_counter()
    print(f"{context}: {end - start:.4f}s")


def get_argparse() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-r",
        "--secondsPerHash",
        help="The frequence(per second) a hash is generated from the video. If it is 0, will generate every frame's hash",
        default=0,
        type=float,
    )
    ap.add_argument(
        "-s",
        "--downsampleFrameDimension",
        metavar="Downsample_Frame_Dimension",
        help="Resolution to downsample the video to before hashing frames.. If it is 0, will use the original dimension of the video to hash",
        default=0,
        type=int,
    )
    return ap


def run_benchmark(
    secondsPerHash: int,
    downsampleFrameDimension: int,
):
    with timer("Python hashing time") as pt:
        python_features = run_python(
            secondsPerHash, downsampleFrameDimension
        )
    feature_size = 0
    feature_size = sum(len(feature) for feature in python_features)
    python_time = pt()
    print(
        "  Total hash:",
        feature_size,
        "Per hash:",
        f"{1000*python_time /  feature_size:.4f}ms",
    )
    with timer("CPP hashing time") as ct:
        run_cpp(secondsPerHash, downsampleFrameDimension)
    cpp_time = ct()
    print(
        "  Total hash:",
        feature_size,
        "Per hash:",
        f"{1000*cpp_time /  feature_size:.4f}ms",
    )
    if downsampleFrameDimension != 0:
        print(
            "Calculate deviations in downsampled hashes, since hash resolution is non-native"
        )
        with timer("Original resolution Python hashing time"):
            original_features = run_python(secondsPerHash, 0)
        total_dist = 0
        mis_match = 0
        for original_hash, downsample_hash in zip(original_features, python_features):
            for original_frame, downsample_frame in zip(original_hash, downsample_hash):
                dist = original_frame.hamming_distance(downsample_frame)
                if dist >= VPDQ_MATCH_DIST:
                    mis_match += 1
                total_dist += dist
        print(
            f"  Number of mismatches: {mis_match}, {mis_match/ feature_size:.2f} percent in total."
        )
        print(f"  Average {total_dist/ feature_size:.2f} hamming distance away.")


def run_python(
    secondsPerHash: int,
    downsampleFrameDimension: int,
):
    hash_list = []
    for file in os.listdir(VIDEOS):
        if file.endswith(".mp4"):
            hash_list.append(
                vpdq.computeHash(
                    str(VIDEOS / file),
                    seconds_per_hash=secondsPerHash,
                    downsample_width=downsampleFrameDimension,
                    downsample_height=downsampleFrameDimension,
                )
            )
    return hash_list


def run_cpp(
    secondsPerHash: int,
    downsampleFrameDimension: int,
):
    Path.mkdir(OUTPUT, exist_ok=True)
    for file in os.listdir(VIDEOS):
        if file.endswith(".mp4"):
            subprocess.check_call(
                [
                    str(CPP_EXEC),
                    "-r",
                    str(secondsPerHash),
                    "-d",
                    str(OUTPUT),
                    "-s",
                    str(downsampleFrameDimension),
                    "-i",
                    str(VIDEOS) + "/" + file,
                ],
            )


def main():
    ap = get_argparse()
    ns = ap.parse_args()
    run_benchmark(**ns.__dict__)


if __name__ == "__main__":
    main()
