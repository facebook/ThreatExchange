# Copyright (c) Meta Platforms, Inc. and affiliates.

import subprocess
import os
import sys
import argparse
from pathlib import Path

VPDQ_BIN_DIR = Path(__file__).parent.parent
MATCH_HASHES_BRUTE_BIN = VPDQ_BIN_DIR / "build/cpp/apps/match-hashes-brute"


def get_argparse() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )

    ap.add_argument(
        "-f",
        "--queryHashFolder",
        metavar="QUERY_HASH_Folder_PATH",
        help="Query Hashes Folder's Name",
        type=dir_path,
        required=True,
    )
    ap.add_argument(
        "-i",
        "--targetHashFile",
        metavar="TARGET_HASH_FILE_PATH",
        help="Target Hash file path for comparing with the query hashes",
        required=True,
    )

    ap.add_argument(
        "-t",
        "--matchDistanceTolerance",
        metavar="Matching_distanceTolerance",
        help="The hamming distance tolerance of between two frames. If the hamming distance is bigger than the tolerance, it will be considered as unmatched",
        default="31",
        type=int,
    )
    ap.add_argument(
        "-q",
        "--qualityTolerance",
        metavar="Matching_qualityTolerance",
        help="The quality tolerance of matching two frames. If either frames is below this quality level then they will not be compared",
        default="50",
        type=int,
    )
    ap.add_argument(
        "-v",
        "--verbose",
        help="If verbose, will print detailed information.",
        action="store_true",
    )
    return ap


def dir_path(string):
    if os.path.isdir(string):
        return string
    else:
        raise argparse.ArgumentTypeError(f"readable_dir: {string} is not a valid path")


def main():
    ap = get_argparse()
    args = ap.parse_args()
    targetHashFile = args.targetHashFile
    queryHashFolder = args.queryHashFolder
    verbose = args.verbose
    distanceTolerance = str(args.matchDistanceTolerance)
    qualityTolerance = str(args.qualityTolerance)
    for file in os.listdir(queryHashFolder):
        if file.endswith(".txt"):
            print(
                "\nMatching Target:"
                + targetHashFile
                + "\n Query: "
                + f"{queryHashFolder}/{file}"
            )
            query_file = f"{queryHashFolder}/{file}"
            if verbose:
                subprocess.call(
                    [
                        MATCH_HASHES_BRUTE_EXE,
                        "-v",
                        query_file,
                        targetHashFile,
                        distanceTolerance,
                        qualityTolerance,
                    ]
                )
            else:
                subprocess.call(
                    [
                        MATCH_HASHES_BRUTE_EXE,
                        query_file,
                        targetHashFile,
                        distanceTolerance,
                        qualityTolerance,
                    ]
                )


if __name__ == "__main__":
    main()
