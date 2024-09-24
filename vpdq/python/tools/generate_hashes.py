# Copyright (c) Meta Platforms, Inc. and affiliates.

import vpdq  # type: ignore
from pathlib import Path
from typing import Union, Sequence
import glob
import argparse

DIR = Path(__file__).parent
VPDQ_DIR = DIR.parent.parent
PROJECT_DIR = Path(__file__).parents[3]


def get_argparse() -> argparse.ArgumentParser:
    default_video_folder = PROJECT_DIR / Path("tmk/sample-videos")
    default_hash_folder = VPDQ_DIR / "sample-hashes"

    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )

    ap.add_argument(
        "-i",
        "--inputVideoFolder",
        help="Video folder to hash recursively",
        type=dir_path,
        default=default_video_folder,
    )

    ap.add_argument(
        "-d",
        "--outputHashFolder",
        help="Query Hashes Folder's Name",
        type=dir_path,
        default=default_hash_folder,
    )

    ap.add_argument(
        "--overwrite",
        help="Overwrite existing hashes in the folder.",
        type=bool,
        default=False,
        action=argparse.BooleanOptionalAction,
    )

    ap.add_argument(
        "-v",
        "--verbose",
        help="Print verbose output.",
        type=bool,
        default=False,
        action=argparse.BooleanOptionalAction,
    )

    return ap


def dir_path(path: Union[Path, str]) -> Path:
    path = Path(path)
    if not Path(path).is_dir():
        raise argparse.ArgumentTypeError(f"{path} is not a valid path")
    return path


def generate_hashes(
    output_folder: Path,
    input_filepaths: Sequence[Path],
    overwrite: bool = False,
    verbose: bool = False,
    downsample_width: int = 0,
    downsample_height: int = 0,
) -> int:
    """
    Generate vpdq hashes for the test videos
    and write them to files in output_folder

    If overwrite is set, it will overwrite existing hashes in the folder.

    Returns the number of files hashed and written.
    """
    hash_count = 0
    for fileStr in input_filepaths:
        file = Path(fileStr)
        if downsample_width > 0 and downsample_height > 0:
            output_hash_filename = (
                output_folder
                / f"{file.stem}-{downsample_width}x{downsample_height}.txt"
            )
        else:
            output_hash_filename = output_folder / f"{file.stem}.txt"

        if not overwrite and output_hash_filename.exists():
            if verbose:
                print(
                    f"Hash file {output_hash_filename.name} already exists. Skipping."
                )
            continue

        vpdq_hash = vpdq.computeHash(
            input_video_filename=file,
            seconds_per_hash=0,
            downsample_width=downsample_width,
            downsample_height=downsample_height,
        )

        # Overwrite existing hashes if overwrite is set
        filemode = "w+t" if overwrite else "x+t"
        with open(output_hash_filename, filemode) as output_file:
            for feature in vpdq_hash:
                output_file.write(
                    f"{feature.frame_number},{feature.quality},{vpdq.hash_to_hex(feature.hash)},{feature.timestamp:.3f}\n"
                )
        hash_count += 1
    return hash_count


def get_test_file_paths(video_folder: Path) -> Sequence[Path]:
    test_files = []
    for fileStr in glob.iglob(f"{video_folder}/**/*.mp4", recursive=True):
        file = Path(fileStr)
        if not (video_folder / f"{file.name}").is_file():
            print(f"Video file {file.name} doesn't exist. Skipping.")
            continue
        test_files.append(file)
    assert len(test_files) > 0
    return test_files


def main():
    """
    Generate hashes for the sample videos.
    This can be used to update the hashes for the sample videos if vpdq is changed.
    """
    ap = get_argparse()
    args = ap.parse_args()
    inputVideoFolder = args.inputVideoFolder
    outputHashFolder = args.outputHashFolder
    overwrite = args.overwrite
    verbose = args.verbose

    test_files = get_test_file_paths(inputVideoFolder)

    print(f"Generating hashes for videos in {inputVideoFolder}")
    print(f"Outputting hashes to {outputHashFolder}")
    print("Overwriting existing hashes.") if overwrite else print("")

    hash_count = generate_hashes(
        outputHashFolder, test_files, overwrite=overwrite, verbose=verbose
    )
    print(f"Generated {hash_count} new hashes.")

    # Generate 128x128 downsampled hashes for the sample videos
    downsampled_hash_count = generate_hashes(
        outputHashFolder,
        test_files,
        overwrite=overwrite,
        verbose=verbose,
        downsample_width=128,
        downsample_height=128,
    )

    print(f"Generated {downsampled_hash_count} new downsampled hashes.")


if __name__ == "__main__":
    main()
