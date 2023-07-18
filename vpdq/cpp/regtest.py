# Copyright (c) Meta Platforms, Inc. and affiliates.

import subprocess
import sys
import argparse
from pathlib import Path
from tempfile import TemporaryDirectory
from shutil import copyfile
import glob
import platform

DIR = Path(__file__).parent
VPDQ_DIR = DIR.parent
SAMPLE_HASHES_DIR = VPDQ_DIR / "sample-hashes"
EXEC_DIR = VPDQ_DIR / "cpp/build"


def get_os():
    if platform.system() == "Windows":
        return "Windows"
    elif platform.system() == "Darwin":
        return "Darwin"
    elif platform.system() == "Linux":
        return "Linux"
    else:
        raise Exception("Unsupported OS")


def get_argparse() -> argparse.ArgumentParser:
    DEFAULT_SAMPLE_VIDEOS_DIR = VPDQ_DIR.parent / "tmk/sample-videos"

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
        type=Path,
    )
    ap.add_argument(
        "-i",
        "--inputVideoFolder",
        metavar="INPUTPUT_VIDEO_FOLDER_PATH",
        help="Input Video Folder",
        default=DEFAULT_SAMPLE_VIDEOS_DIR,
        type=Path,
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


def main():
    hashVideoExecutable = EXEC_DIR / "vpdq-hash-video"
    matchHashesExecutable = EXEC_DIR / "match-hashes-byline"

    OS = get_os()

    if OS == "Windows":
        hashVideoExecutable = Path(f"{hashVideoExecutable}.exe")
        matchHashesExecutable = Path(f"{matchHashesExecutable}.exe")

    if not hashVideoExecutable.exists() or not matchHashesExecutable.exists():
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

    if not inputVideoFolder.exists():
        raise argparse.ArgumentTypeError(
            f"inputVideoFolder: {inputVideoFolder} does not exist."
        )

    with TemporaryDirectory() as tempOutputHashFolder:
        # Write the files to temp
        # If outputHashFolder is specified then
        # copy the output files there, overwriting existing files

        tempOutputHashFolder = Path(tempOutputHashFolder)
        if outputHashFolder is not None:
            if not outputHashFolder.exists():
                print(f"Creating output directory at {outputHashFolder}")
                outputHashFolder.mkdir(parents=True, exist_ok=True)
            print(f"Writing output to directory: {outputHashFolder}")
        else:
            print(f"Writing output to temp directory: {tempOutputHashFolder}")
        # TODO: Add more general options for other video extensions.
        for fileStr in glob.iglob(f"{inputVideoFolder}/**/*.mp4", recursive=True):
            file = Path(fileStr)

            # Create output hash file or overwrite existing file
            # This is hardcoded in cpp, and it
            # does not create the file if it does not exist:
            #
            # vpdq-hash-video.cpp:
            #
            # // Strip containing directory:
            # std::string b = basename(inputVideoFileName, "/");
            # // Strip file extension:
            # b = stripExtension(b, ".");
            # outputHashFileName = outputDirectory + "/" + b + ".txt";
            outputHashFile = tempOutputHashFolder / f"{file.stem}.txt"
            with open(outputHashFile, "x+t"):
                pass

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
            ]

            if verbose:
                command.insert(1, "-v")

            try:
                hash_proc = subprocess.run(
                    command,
                    check=True,
                    capture_output=True,
                    shell=(OS == "Windows"),
                )
                if verbose:
                    # This will print all PDQHashes e.g.
                    # PDQHash: ebcc8b06b0666ea34cf9b85972a983a4f94668af05fc9d52aa9662f975499514
                    # selectframe 563
                    print(str(hash_proc.stdout, "utf-8"))
            except subprocess.CalledProcessError as e:
                print(e.cmd)
                print(str(e.stderr, "utf-8"))
                sys.exit(1)

            if outputHashFolder is not None:
                copyfile(outputHashFile, Path(outputHashFolder / outputHashFile.name))
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
                command.insert(1, "-v")

            try:
                match_proc = subprocess.run(
                    command,
                    check=True,
                    capture_output=True,
                    shell=(OS == "Windows"),
                )
                if verbose:
                    # This will print all PDQHashes e.g.
                    # Line 201 Hash1: da4b380330b725b4a5f08ff03d0f6949da4fd2d3e7c8e4930fa7b80662a17c4e
                    # Hash2: da4b380330b725b4a5f08ff03d0f6949da4fd2d3e7c8e4930fa7b80662a17c4e match
                    print(str(match_proc.stdout, "utf-8"))
            except subprocess.CalledProcessError as e:
                print(e.cmd)
                print(str(e.stderr, "utf-8"))
                sys.exit(1)


if __name__ == "__main__":
    main()
