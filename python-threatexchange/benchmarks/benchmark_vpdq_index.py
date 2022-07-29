# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Script to benchmark performance of vpdq brute_force, index with faiss and faiss only
"""

import argparse
import time

from enum import Enum
from contextlib import contextmanager, nullcontext
from threatexchange.extensions.vpdq.vpdq_brute_matcher import match_VPDQ_hash_brute
from threatexchange.extensions.vpdq.tests.utils import get_random_VPDQs
from threatexchange.extensions.vpdq.vpdq_faiss import VPDQHashIndex
from threatexchange.extensions.vpdq.vpdq_util import (
    vpdq_to_json,
    VPDQ_QUALITY_THRESHOLD,
    VPDQ_DISTANCE_THRESHOLD,
)

import typing as t

from threatexchange.extensions.vpdq.vpdq_index import VPDQIndex
from threatexchange.extensions.vpdq.video_vpdq import VideoVPDQSignal


Oint = t.Optional[int]


class IndexType(Enum):
    BRUTE_FORCE = "brute_force"
    FLAT = "flat"
    SIGNAL_TYPE = "signal_type"

    def __str__(self) -> str:
        return self.value

@contextmanager
def timer(context: str, print_on_enter: bool = False):
    if print_on_enter:
        print(f"{context}...")
    start = time.perf_counter()
    end = start
    yield lambda: end - start
    end = time.perf_counter()
    print(f"{context}: {end - start:.4f}s")


def run_benchmark(
    test_type: IndexType,
    video_frames: int,
    dataset_size: int,
    query_size: int,
):

    data_generation_timer = nullcontext()
    if video_frames * dataset_size > 10000:
        data_generation_timer = timer("Generating data", True)
    with data_generation_timer:
        hashes = [get_random_VPDQs(video_frames) for _ in range(dataset_size)]
    if test_type == IndexType.SIGNAL_TYPE:
        build = lambda: build_signal(hashes)
    elif test_type == IndexType.BRUTE_FORCE:
        build = lambda: hashes
    elif test_type == IndexType.FLAT:
        build = lambda: build_flat(hashes)
    else:
        raise ValueError("Invalid test type")

    with timer("build"):
        index = build()

    query_generation_timer = nullcontext()
    if query_size > 10000:
        query_generation_timer = timer("Generating queries", True)
    with query_generation_timer:
        hq = get_random_VPDQs(query_size)
    if test_type == IndexType.SIGNAL_TYPE:
        query = lambda: sigal_match(hq, index)
    elif test_type == IndexType.BRUTE_FORCE:
        query = lambda: brute_force_match(hq, index)
    elif test_type == IndexType.FLAT:
        query = lambda: index.search_with_distance_in_result(
            hq, VPDQ_DISTANCE_THRESHOLD
        )
    
    with timer("query") as t:
        query()
    query_time = t()
    print(f"  Per query: {1000 * query_time / query_size:.4f}ms")


def build_flat(videos):
    index = VPDQHashIndex()
    for v in videos:
        index.add_single_video(v)
    return index


def build_signal(hashes):
    index = VPDQIndex()
    for h in hashes:
        index.add(vpdq_to_json(h), object())
    return index


def sigal_match(hash, index):
    index.query(vpdq_to_json(hash))


def brute_force_match(query, hashes):
    for hash in hashes:
        match_VPDQ_hash_brute(
            query, hash, VPDQ_QUALITY_THRESHOLD, VPDQ_DISTANCE_THRESHOLD
        )


def get_argparse():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--video-frames",
        "-v",
        type=int,
        default=500,
        help="How many frames in each video",
    )
    ap.add_argument(
        "--dataset-size",
        "-n",
        type=int,
        default=2000,
        help="How large to make the dataset",
    )
    ap.add_argument(
        "--query-size",
        "-q",
        type=int,
        default=1000,
        help="number of queries",
    )
    ap.add_argument(
        "test_type",
        choices=list(IndexType),
        type=IndexType,
        help="what type of index to test",
    )
    return ap


def main():
    ap = get_argparse()
    ns = ap.parse_args()
    run_benchmark(**ns.__dict__)


if __name__ == "__main__":
    main()
