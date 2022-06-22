import subprocess
import os
import sys
import argparse

def get_argparse() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )

    ap.add_argument(
        "-f",
        "--queryHashFolder",
        metavar="QUERY_HASH_Folder_PATH",
        help="Query Hashes Folder's Name"
        )
    ap.add_argument(
        "-i",
        "--targetHashFile",
        metavar="TARGET_HASH_FILE_PATH",
        help="Target Hash file path for comparing with the query hashes"
        )

    ap.add_argument(
        "-t",
        "--matchDistanceTolerance",
        metavar="Matching_Distance_Tolerance",
        help="The hamming distance tolerance of between two frames. If the hamming distance is bigger than the tolerance, it will be considered as unmatched",
        default="31"
        )
    ap.add_argument(
        "-q",
        "--qualityTolerance",
        metavar="Matching_Quality_Tolerance",
        help="The quality tolerance of matching two frames. If either frames is below this quality level then they will not be compared",
        default="50"
        )
    ap.add_argument(
        "-v",
        "--verbose",
        metavar="Verbose",
        help="If verbose, will print detailed information.",
        default= False
        )
    return ap

def main():
    ap = get_argparse()
    args, unknownargs = ap.parse_known_args(sys.argv)
    targetHashFile = args.targetHashFile
    queryHashFolder = args.queryHashFolder
    verbose = args.verbose
    distance_tolerance = args.matchDistanceTolerance
    quality_tolerance = args.qualityTolerance
    for file in os.listdir(queryHashFolder):
        if file.endswith('.txt'):
            print("\nMatching Target:"+targetHashFile + "\n Query: " + f"{queryHashFolder}/{file}")
            query_file = f"{queryHashFolder}/{file}"
            if verbose:
                subprocess.call([
                    "./build/match-hashes-brute",
                    "-v",
                    query_file,
                    targetHashFile,
                    distance_tolerance,
                    quality_tolerance
                    ])
            else:
                subprocess.call([
                    "./build/match-hashes-brute",
                    query_file,
                    targetHashFile,
                    distance_tolerance,
                    quality_tolerance
                    ])



if __name__ == "__main__":
    main()
