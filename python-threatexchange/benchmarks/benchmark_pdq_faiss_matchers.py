# Copyright (c) Meta Platforms, Inc. and affiliates.

import argparse
import binascii
import time
import pickle

import numpy
import faiss

from threatexchange.signal_type.pdq.pdq_utils import BITS_IN_PDQ

from threatexchange.signal_type.pdq.pdq_faiss_matcher import (
    PDQFlatHashIndex,
    PDQMultiHashIndex,
)

parser = argparse.ArgumentParser(
    description="Run basic benchmarks comparing PDQHashIndex implementations using faiss",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)

parser.add_argument(
    "--faiss-threads",
    type=int,
    default=1,
    help="number of threads for faiss to use while searching",
)
parser.add_argument(
    "--dataset-size",
    type=int,
    default=250000,
    help="number of hashes to generate for the dataset to search against",
)
parser.add_argument(
    "--num-queries",
    type=int,
    default=1000,
    help="number of queries to generate for each search",
)
parser.add_argument(
    "--thresholds",
    type=int,
    default=[0, 15, 31, 47],
    choices=range(256),
    nargs="+",
    metavar="THRESHOLDS",
    help="PDQ similarity threshold values to benchmark with",
)
parser.add_argument("--seed", type=int, help="seed for random number generator")

args = parser.parse_args()

######
# Print Benchmark Settings
######

print("Benchmark: PDQ Faiss Matcher Comparison")
print("")
print("Options:")
for arg in vars(args):
    print("\t", arg, ": ", getattr(args, arg))
print("")

######
# Set up environment and helpers
######

faiss.omp_set_num_threads(args.faiss_threads)
seed = args.seed if args.seed else time.time_ns()
rng = numpy.random.default_rng(seed)
if args.seed is None:
    print("using random seed of ", seed)
    print("use --seed ", seed, " to rerun with same random values")
    print("")


def generate_random_hash():
    """
    returns a random 256 bit PDQ hash as a hexstring of 64 characters
    """
    hash_bytes = rng.bytes(BITS_IN_PDQ // 8)
    return binascii.hexlify(hash_bytes).decode()


def generate_random_distance_mask(hamming_distance):
    """
    returns a random numpy array of uint8s that can be used as bitwise mask
    to generate a hash with the given hamming distance
    """
    ones = numpy.ones(hamming_distance, dtype=numpy.uint8)
    bitmask = numpy.pad(
        ones, (0, BITS_IN_PDQ - hamming_distance), "constant", constant_values=0
    )
    return numpy.packbits(rng.permutation(bitmask))


def generate_random_hash_with_hamming_distance(original_hash, desired_hamming_distance):
    """
    returns a random 256 bit PDQ hash as a hexstring of 64 characters that is the given
    hamming distance from the provided original hash
    """
    original_hash_bytes = numpy.frombuffer(
        binascii.unhexlify(original_hash), dtype=numpy.uint8
    )
    mask = generate_random_distance_mask(desired_hamming_distance)
    new_hash_bytes = numpy.bitwise_xor(original_hash_bytes, mask).tobytes()
    return binascii.hexlify(new_hash_bytes).decode()


######
# Generate Random Dataset and Build Indexes
######

dataset = [generate_random_hash() for _ in range(args.dataset_size)]


custom_ids = [i + 100_000_000_000_000 for i in range(args.dataset_size)]

start_build_flat_hash_index = time.time()
flat_index = PDQFlatHashIndex()
flat_index.add(dataset, custom_ids=custom_ids)
serialized_flat_index = pickle.dumps(flat_index)
end_build_flat_hash_index = time.time()

start_build_multi_hash_index = time.time()
multi_index = PDQMultiHashIndex()
multi_index.add(dataset, custom_ids=custom_ids)
serialized_multi_index = pickle.dumps(multi_index)
end_build_multi_hash_index = time.time()

print("Building Stats:")

print(
    "\tPDQFlatHashIndex: time to build (s): ",
    end_build_flat_hash_index - start_build_flat_hash_index,
)
print(
    f"\tPDQFlatHashIndex: approximate size: {len(serialized_flat_index) // 1024:,d}KB"
)
print(
    "\tPDQMultiHashIndex: time to build (s): ",
    end_build_multi_hash_index - start_build_multi_hash_index,
)
print(
    f"\tPDQMultiHashIndex: approximate size: {len(serialized_multi_index) // 1024:,d}KB"
)
print("")

######
# Run benchmarks for each requested search threshold
######
for threshold in args.thresholds:
    print("Benchmarks for threshold: ", threshold)

    # Create queries with hamming distance of threshold compared to their search targets
    search_targets = rng.choice(dataset, size=args.num_queries)
    queries = [
        generate_random_hash_with_hamming_distance(target, threshold)
        for target in search_targets
    ]

    # Benchmark Searching Indexes
    start_flat_search = time.time()
    flat_results = flat_index.search(queries, threshold)
    end_flat_search = time.time()

    start_multi_search = time.time()
    multi_results = multi_index.search(queries, threshold)
    end_multi_search = time.time()

    def count_targets_found(targets, queries, results):
        """
        Checks that each element of the provided search results list contains
        the associated target for that query, warning if it does not.

        Returns the number of targets that were found in their corresponding
        results
        """
        found_targets = 0
        for target, query, result in zip(targets, queries, results):
            if target not in result:
                print(
                    "Query missed target in result: query=",
                    query,
                    "target=",
                    target,
                    "result=",
                    result,
                )
            else:
                found_targets += 1
        return found_targets

    flat_found_targets = count_targets_found(search_targets, queries, flat_results)
    multi_found_targets = count_targets_found(search_targets, queries, multi_results)

    print(
        "\tPDQFlatHashIndex - Total Time to search  (s): ",
        end_flat_search - start_flat_search,
    )
    print(
        "\tPDQMultiHashIndex - Total Time to search  (s): ",
        end_multi_search - start_multi_search,
    )
    print(
        "\tPDQFlatHashIndex - Precent of targets found: ",
        flat_found_targets / len(queries) * 100,
    )
    print(
        "\tPDQMultiHashIndex - Precent of targets found: ",
        multi_found_targets / len(queries) * 100,
    )

    print("")
