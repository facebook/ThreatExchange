import subprocess
import os
import sys
import argparse


def get_argparse() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("-f", "--ffmpegPath", metavar="FFMPEG_PATH", help="ffmpeg path")
    ap.add_argument(
        "-r",
        "--secondsPerHash",
        metavar="POSITIVE_INTEGER",
        help="The frequence(per second) a hash is generated from the video",
        default="1",
    )
    ap.add_argument(
        "-d",
        "--outputHashFolder",
        metavar="OUTPUT_HASH_Folder_PATH",
        help="Output Hash Folder's Name",
        default="/ThreatExchange/vpdq/output-hashes",
    )
    ap.add_argument(
        "-i",
        "--inputVideoFolder",
        metavar="INPUTPUT_VIDEO_FOLDER_PATH",
        help="Input Video Folder",
        default="/ThreatExchange/tmk/sample-videos",
    )
    ap.add_argument(
        "-s",
        "--downsampleFrameDimension",
        metavar="Downsample_Frame_Dimension",
        help="Resolution to downsample the video to before hashing frames.. If it is 0, will use the original dimension of the video to hash",
        default="0",
    )
    ap.add_argument(
        "-t",
        "--matchDistanceTolerance",
        metavar="Matching_distanceTolerance",
        help="The hamming distance tolerance of between two frames. If the hamming distance is bigger than the tolerance, it will be considered as unmatched",
        default="10",
    )
    ap.add_argument(
        "-q",
        "--qualityTolerance",
        metavar="Matching_qualityTolerance",
        help="The quality tolerance of matching two frames. If either frames is below this quality level then they will not be compared",
        default="80",
    )
    ap.add_argument(
        "-v",
        "--verbose",
        metavar="Verbose",
        help="If verbose, will print detailed information.",
        default=False,
    )
    return ap


def main():
    ap = get_argparse()
    args, unknownargs = ap.parse_known_args(sys.argv)
    inputVideoFolder = args.inputVideoFolder
    outputHashFolder = args.outputHashFolder
    ffmpegPath = args.ffmpegPath
    secondsPerHash = args.secondsPerHash
    downsampleFrameDimension = args.downsampleFrameDimension
    verbose = args.verbose
    # TODO: Add more general options for other video encodings.
    for file in os.listdir(inputVideoFolder):
        if file.endswith(".mp4"):
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
    distanceTolerance = args.matchDistanceTolerance
    qualityTolerance = args.qualityTolerance
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
