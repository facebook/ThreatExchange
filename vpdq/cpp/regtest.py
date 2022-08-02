import subprocess
import os
import sys
import argparse


def get_argparse() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description=__doc__
    )
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
        default="/ThreatExchange/vpdq/output-hashes",
        type=dir_path,
    )
    ap.add_argument(
        "-i",
        "--inputVideoFolder",
        metavar="INPUTPUT_VIDEO_FOLDER_PATH",
        help="Input Video Folder",
        default="/ThreatExchange/tmk/sample-videos",
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
        default="10",
        type=int,
    )
    ap.add_argument(
        "-q",
        "--qualityTolerance",
        metavar="Matching_qualityTolerance",
        help="The quality tolerance of matching two frames. If either frames is below this quality level then they will not be compared",
        default="80",
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
    inputVideoFolder = args.inputVideoFolder
    outputHashFolder = args.outputHashFolder
    ffmpegPath = args.ffmpegPath
    secondsPerHash = str(args.secondsPerHash)
    downsampleFrameDimension = str(args.downsampleFrameDimension)
    verbose = args.verbose
    # TODO: Add more general options for other video encodings.
    for file in os.listdir(inputVideoFolder):
        if file.endswith(".mp4"):
            if verbose:
                subprocess.call(
                    [
                        "./build/vpdq-hash-video",
                        "-v",
                        "-f",
                        ffmpegPath,
                        "-r",
                        secondsPerHash,
                        "-d",
                        outputHashFolder,
                        "-s",
                        downsampleFrameDimension,
                        "-i",
                        inputVideoFolder + "/" + file,
                    ]
                )
            else:
                subprocess.call(
                    [
                        "./build/vpdq-hash-video",
                        "-f",
                        ffmpegPath,
                        "-r",
                        secondsPerHash,
                        "-d",
                        outputHashFolder,
                        "-s",
                        downsampleFrameDimension,
                        "-i",
                        inputVideoFolder + "/" + file,
                    ]
                )

    cdir = os.getcwd()
    pdir = os.path.dirname(cdir)
    sample = pdir + ("/sample-hashes")
    output = outputHashFolder
    distanceTolerance = str(args.matchDistanceTolerance)
    qualityTolerance = str(args.qualityTolerance)
    for file in os.listdir(sample):
        if file.endswith(".txt"):
            print("\nMatching File " + file)
            sampleFile = f"{sample}/{file}"
            outputFile = f"{output}/{file}"
            if verbose:
                subprocess.call(
                    [
                        "./build/match-hashes-byline",
                        "-v",
                        sampleFile,
                        outputFile,
                        distanceTolerance,
                        qualityTolerance,
                    ]
                )
            else:
                subprocess.call(
                    [
                        "./build/match-hashes-byline",
                        sampleFile,
                        outputFile,
                        distanceTolerance,
                        qualityTolerance,
                    ]
                )


if __name__ == "__main__":
    main()
