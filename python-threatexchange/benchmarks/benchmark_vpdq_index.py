# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Script to benchmark performance of vpdq brute_force, index with faiss and faiss only
"""

import argparse
import time
import pickle
import numpy as np

from enum import Enum
from contextlib import contextmanager, nullcontext
from threatexchange.extensions.vpdq.vpdq_brute_matcher import match_VPDQ_hash_brute
from threatexchange.extensions.vpdq.tests.utils import get_random_vpdq_features
from threatexchange.extensions.vpdq.vpdq_faiss import VPDQHashIndex
from threatexchange.extensions.vpdq.vpdq_util import (
    vpdq_to_json,
    VPDQ_QUALITY_THRESHOLD,
    VPDQ_DISTANCE_THRESHOLD,
)

import typing as t
import random
from threatexchange.extensions.vpdq.vpdq_index import VPDQIndex


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
    average_frames: int,
    jitter_noise: int,
    dataset_size: int,
    query_size: int,
):
    assert jitter_noise <= average_frames
    assert average_frames > 0
    assert dataset_size > 0
    assert query_size > 0

    data_generation_timer = nullcontext()
    if average_frames * dataset_size > 10000:
        data_generation_timer = timer("Generating data", True)
    with data_generation_timer:
        hashes = [
            get_random_vpdq_features(
                average_frames + random.randint(-jitter_noise, jitter_noise)
            )
            for _ in range(dataset_size)
        ]
    if test_type == IndexType.SIGNAL_TYPE:
        build = lambda: build_signal(hashes)
    elif test_type == IndexType.BRUTE_FORCE:
        build = lambda: hashes
    elif test_type == IndexType.FLAT:
        build = lambda: build_flat(hashes)

    start_build = time.perf_counter()
    if test_type == IndexType.SIGNAL_TYPE:
        index = build_signal(hashes)
        serialized = pickle.dumps(index)
    elif test_type == IndexType.BRUTE_FORCE:
        index = hashes
        serialized = pickle.dumps(index)
    elif test_type == IndexType.FLAT:
        index = build_flat(hashes)
        serialized = pickle.dumps(index)
    build_time = time.perf_counter() - start_build
    
    print(f"Build time: {build_time:.4f}s")
    print(f"Index size: {len(serialized) // 1024:,d}KB")

    # Generate target queries with known matches
    target_indices = np.random.choice(len(hashes), query_size)
    target_hashes = [hashes[i] for i in target_indices]
    
    with timer("query") as t:
        if test_type == IndexType.SIGNAL_TYPE:
            results = [signal_match(h, index) for h in target_hashes]
        elif test_type == IndexType.BRUTE_FORCE:
            results = [brute_force_match(h, index) for h in target_hashes]
        elif test_type == IndexType.FLAT:
            results = [
                index.search_with_distance_in_result(h, VPDQ_DISTANCE_THRESHOLD)
                for h in target_hashes
            ]
    
    query_time = t()
    matches_found = sum(1 for r in results if len(r) > 0)
    print(f"  Per query: {1000 * query_time / query_size:.4f}ms")
    print(f"  Match rate: {100 * matches_found / query_size:.2f}%")


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


def signal_match(hash, index):
    return index.query(vpdq_to_json(hash))


def brute_force_match(query, hashes):
    results = []
    for hash in hashes:
        if match_VPDQ_hash_brute(
            query, hash, VPDQ_QUALITY_THRESHOLD, VPDQ_DISTANCE_THRESHOLD
        ):
            results.append(hash)
    return results


def get_argparse():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--average-frames",
        "-f",
        type=int,
        default=500,
        help="How many frames in each video",
    )
    ap.add_argument(
        "--jitter-noise",
        "-j",
        type=int,
        default=50,
        help="How many frames varies between each video in uniformal distribution",
    )
    ap.add_argument(
        "--dataset-size",
        "-v",
        type=int,
        default=2000,
        help="How many videos in the dataset",
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
