# Copyright (c) Meta Platforms, Inc. and affiliates.

import subprocess
import sys
import argparse
from pathlib import Path
import glob

DIR = Path(__file__).parent
VPDQ_DIR = DIR.parent
SAMPLE_HASHES_DIR = VPDQ_DIR / "sample-hashes"
EXEC_DIR = VPDQ_DIR / "cpp/build"


def get_argparse() -> argparse.ArgumentParser:
    DEFAULT_OUTPUT_HASHES_DIR = VPDQ_DIR / "output-hashes"
    DEFAULT_SAMPLE_VIDEOS_DIR = VPDQ_DIR.parent / "tmk/sample-videos"

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "-f",
        "--ffmpegPath",
        metavar="FFMPEG_PATH",
        help="Specific path to ffmpeg you want to use",
        default="ffmpeg",
    )
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
        default=DEFAULT_OUTPUT_HASHES_DIR,
        type=dir_path,
    )
    ap.add_argument(
        "-i",
        "--inputVideoFolder",
        metavar="INPUTPUT_VIDEO_FOLDER_PATH",
        help="Input Video Folder",
        default=DEFAULT_SAMPLE_VIDEOS_DIR,
        type=dir_path,
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


def dir_path(string):
    if Path(string).is_dir():
        return string
    raise argparse.ArgumentTypeError(
        f"readable_dir: {string} is not a valid directory path"
    )


def main():
    hashVideoExecutable = EXEC_DIR / "vpdq-hash-video"
    matchHashesExecutable = EXEC_DIR / "match-hashes-byline"

    if not hashVideoExecutable.exists() or not matchHashesExecutable.exists():
        print(
            "Error: Hashing executable/s not found. Build vpdq before running regtest."
        )
        sys.exit(1)

    ap = get_argparse()
    args = ap.parse_args()
    inputVideoFolder = Path(args.inputVideoFolder)
    outputHashFolder = Path(args.outputHashFolder)
    ffmpegPath = args.ffmpegPath
    secondsPerHash = str(args.secondsPerHash)
    downsampleFrameDimension = str(args.downsampleFrameDimension)
    distanceTolerance = str(args.matchDistanceTolerance)
    qualityTolerance = str(args.qualityTolerance)
    verbose = args.verbose

    if not inputVideoFolder.exists():
        raise argparse.ArgumentTypeError(
            f"inputVideoFolder: {inputVideoFolder} does not exist."
        )

    outputHashFolder.mkdir(parents=True, exist_ok=True)

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

        with open(outputHashFolder / f"{file.stem}.txt", "w"):
            pass

        command = [
            hashVideoExecutable,
            "-f",
            ffmpegPath,
            "-r",
            secondsPerHash,
            "-d",
            outputHashFolder,
            "-s",
            downsampleFrameDimension,
            "-i",
            file,
        ]

        if verbose:
            command.insert(1, "-v")

        subprocess.call(command)

    for outputFileStr in glob.iglob(f"{outputHashFolder}/**/*.txt", recursive=True):
        outputFile = Path(outputFileStr)
        sampleFile = SAMPLE_HASHES_DIR / outputFile.name
        print(f"\nMatching File {sampleFile.name}")
        command = [
            matchHashesExecutable,
            sampleFile,
            outputFile,
            distanceTolerance,
            qualityTolerance,
        ]

        if verbose:
            command.insert(1, "-v")

        subprocess.call(command)


if __name__ == "__main__":
    main()
