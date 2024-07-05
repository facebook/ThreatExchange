# Copyright (c) Meta Platforms, Inc. and affiliates.

import os
import subprocess
import sys
import argparse
from pathlib import Path
from tempfile import TemporaryDirectory
from shutil import copyfile
import glob
import platform
from typing import Union
import csv

DIR = Path(__file__).parent
VPDQ_DIR = DIR.parent
SAMPLE_HASHES_DIR = VPDQ_DIR / "sample-hashes"
EXEC_DIR = VPDQ_DIR / "cpp/build/apps"


def get_os() -> str:
    if platform.system() == "Windows":
        return "Windows"
    elif platform.system() == "Darwin":
        return "Darwin"
    elif platform.system() == "Linux":
        return "Linux"
    else:
        print("Unknown OS. Unexpected results may occur.")
        return "Unknown"


def get_argparse() -> argparse.ArgumentParser:
    default_input_videos_dir = VPDQ_DIR.parent / "tmk/sample-videos"

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "-r",
        "--secondsPerHash",
        metavar="NON_NEGATIVE_FLOAT",
        help="The frequence(per second) a hash is generated from the video. If it is 0, will generate every frame's hash",
        default="0",
        type=float,
    )
    ap.add_argument(
        "-d",
        "--outputHashFolder",
        metavar="OUTPUT_HASH_Folder_PATH",
        help="Output Hash Folder's Name",
        type=validate_path,
    )
    ap.add_argument(
        "-i",
        "--inputVideoFolder",
        metavar="INPUTPUT_VIDEO_FOLDER_PATH",
        help="Input Video Folder",
        default=default_input_videos_dir,
        type=validate_path,
    )
    ap.add_argument(
        "-s",
        "--downsampleFrameDimension",
        metavar="Downsample_Frame_Dimension",
        help="Resolution to downsample the video to before hashing frames.. If it is 0, will use the original dimension of the video to hash",
        default="0",
        type=int,
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


def validate_path(path: Union[Path, str], err_msg: Union[str, None] = None) -> Path:
    path = Path(path)
    if not path.exists():
        if err_msg is None:
            err_msg = f"Path {path} does not exist."
        raise argparse.ArgumentTypeError(err_msg)
    return path


def main():
    OS = get_os()

    hashVideoExecutable = EXEC_DIR / "vpdq-hash-video"
    matchHashesExecutable = EXEC_DIR / "match-hashes-byline"

    if OS == "Windows":
        hashVideoExecutable = Path(f"{hashVideoExecutable}.exe")
        matchHashesExecutable = Path(f"{matchHashesExecutable}.exe")

    try:
        validate_path(hashVideoExecutable)
        validate_path(matchHashesExecutable)
    except argparse.ArgumentTypeError as e:
        print(e)
        print(
            "Error: Hashing executable/s not found. Build vpdq before running regtest."
        )
        sys.exit(1)

    ap = get_argparse()
    args = ap.parse_args()
    inputVideoFolder = args.inputVideoFolder
    outputHashFolder = args.outputHashFolder
    secondsPerHash = str(args.secondsPerHash)
    downsampleFrameDimension = str(args.downsampleFrameDimension)
    distanceTolerance = str(args.matchDistanceTolerance)
    qualityTolerance = str(args.qualityTolerance)
    verbose = args.verbose

    # Run the hashing and matching tests for single and multithreaded
    for thread_count in range(0, 2):
        if thread_count == 0:
            num_cpu_cores = os.cpu_count()
            print(f"Number of hashing threads: auto. Probably {num_cpu_cores} threads.")
        else:
            print(f"Number of hashing threads: {thread_count}")
        with TemporaryDirectory() as tempOutputHashFolder:
            tempOutputHashFolder = Path(tempOutputHashFolder)

            # Create output directory if it does not exist and it is specified
            if outputHashFolder is not None:
                if not outputHashFolder.exists():
                    print(f"Creating output directory at {outputHashFolder}")
                    outputHashFolder.mkdir(parents=True)
                print(f"Writing output hash files to directory: {outputHashFolder}")
            else:
                print(f"Writing output to temp directory: {tempOutputHashFolder}")
            # TODO: Add more general options for other video extensions.
            for fileStr in glob.iglob(f"{inputVideoFolder}/**/*.mp4", recursive=True):
                file = Path(fileStr)

                # Create output hash file in a tempdir
                outputHashFile = tempOutputHashFolder / f"{file.stem}.txt"
                outputHashFile.touch(exist_ok=False)

                print(f"\nHashing file {file.name}")
                command = [
                    hashVideoExecutable,
                    "-r",
                    secondsPerHash,
                    "-d",
                    tempOutputHashFolder,
                    "-s",
                    downsampleFrameDimension,
                    "-i",
                    file,
                    "-t",
                    str(thread_count),
                ]

                if verbose:
                    # Print all PDQHashes e.g.
                    # PDQHash: ebcc8b06b0666ea34cf9b85972a983a4f94668af05fc9d52aa9662f975499514
                    # selectframe 563
                    command.insert(1, "-v")

                try:
                    hash_proc = subprocess.run(
                        command,
                        check=True,
                        capture_output=True,
                        shell=(OS == "Windows"),
                    )
                    print(str(hash_proc.stdout, "utf-8"))
                except subprocess.CalledProcessError as e:
                    print(" ".join([str(i) for i in e.cmd]))
                    print(str(e.stderr, "utf-8"))
                    sys.exit(1)

                # Copy hash files to output directory if it is specified
                # This will overwrite existing files with the same
                # name as outputHashFile in the directory
                if outputHashFolder is not None:
                    copyfile(
                        outputHashFile,
                        Path(
                            outputHashFolder
                            / f"{outputHashFile.stem}-{thread_count}thread.txt"
                        ),
                    )

            for outputFileStr in glob.iglob(
                f"{tempOutputHashFolder}/**/*.txt", recursive=True
            ):
                outputFile = Path(outputFileStr)
                sampleFile = Path(SAMPLE_HASHES_DIR / outputFile.name)
                print(
                    f"\nMatching Video {sampleFile.name} from hash file {outputFile.name}"
                )
                command = [
                    matchHashesExecutable,
                    sampleFile,
                    outputFile,
                    distanceTolerance,
                    qualityTolerance,
                ]

                if verbose:
                    # Print all PDQHashes and if they match e.g.
                    # Line 201 Hash1: da4b380330b725b4a5f08ff03d0f6949da4fd2d3e7c8e4930fa7b80662a17c4e
                    # Hash2: da4b380330b725b4a5f08ff03d0f6949da4fd2d3e7c8e4930fa7b80662a17c4e match
                    command.insert(1, "-v")

                try:
                    match_proc = subprocess.run(
                        command,
                        check=True,
                        capture_output=True,
                        shell=(OS == "Windows"),
                    )
                    print(str(match_proc.stdout, "utf-8"))
                except subprocess.CalledProcessError as e:
                    print(e.cmd)
                    print(str(e.stderr, "utf-8"))
                    sys.exit(1)

            # Test that all the features are in frame order
            for outputFileStr in glob.iglob(
                f"{tempOutputHashFolder}/**/*.txt", recursive=True
            ):
                outputFile = Path(outputFileStr)
                with open(outputFile, "r") as f:
                    features = csv.reader(f)
                    oldFrameNumber = -1
                    for feature in features:
                        frameNumber = int(feature[0])
                        assert frameNumber >= 0
                        assert frameNumber > oldFrameNumber
                        assert (oldFrameNumber + 1) == frameNumber
                        oldFrameNumber = frameNumber
            print("All features are in frame order.")
            print("\n--------------------------------------\n")


if __name__ == "__main__":
    main()
