#!/usr/bin/env python
# Copyright (c) Meta Platforms, Inc. and affiliates.
# isort:skip_file

import argparse
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from pdqhashing.hasher.pdq_hasher import PDQHasher
from pdqhashing.types.hash256 import Hash256


class PDQPhotoHasherTool:
    """Tool for computing PDQ hashes of image files (JPEG, PNG, etc.).
    Example use from within pdqhashing directory in Instagram Container:
    python tools/pdq_photo_hasher_tool.py ../media/sample_data/pdq/misc-images/b.jpg --pdq"""

    PROGNAME = "PDQPhotoHasherTool"

    class Context:
        """Helper class for tracking image-to-image deltas"""

        numPDQHash = int()
        pdqHashPrev = Hash256()
        hadError = bool()

        def __init__(self, _numPDQHash, _pdqHashPrev, _hadError) -> None:
            self.numPDQHash = _numPDQHash
            self.pdqHashPrev = _pdqHashPrev
            self.hadError = _hadError

    @classmethod
    def main(cls, args):
        parser = argparse.ArgumentParser(
            prog=cls.PROGNAME,
            description="Create PDQ Photo hashes for provided files. "
            + "Supported filetypes are: JPEG and PNG.",
        )

        parser.add_argument(
            "filenames",
            nargs="*",
            type=str,
            help="Filenames/paths of the files to be processed.",
        )

        parser.add_argument(
            "-i",
            "--filesOnStdin",
            action="store_true",
            help=(
                "Take filenames from stdin, in which case there must be "
                + "no filenames on the command line."
            ),
        )

        parser.add_argument(
            "-d",
            "--doDetailedOutput",
            action="store_true",
            help="Print norm, delta, etc; Otherwise, print just hash, "
            + "quality and filename.",
        )

        parser.add_argument(
            "--pdq",
            dest="doPDQ",
            action="store_true",
            help=(
                "Take filenames from stdin, in which case there must be "
                + "no filenames on the command line."
            ),
        )

        parser.add_argument(
            "--pdqdih",
            dest="doPDQDih",
            action="store_true",
            help="Print all 8 dihedral-transform hashes.",
        )

        parser.add_argument(
            "--pdqdih-across",
            dest="doPDQDihAcross",
            action="store_true",
            help="Print all 8 dihedral-transform hashes, all on one line.",
        )

        parser.add_argument(
            "--no-timings",
            dest="doTimings",
            action="store_false",
            help="Do not compute timing information.",
        )

        parser.add_argument(
            "--k",
            dest="keepGoingAfterErrors",
            action="store_true",
            help="Continue to process next image in case of errors",
        )

        args = parser.parse_args()

        pdqHasher = PDQHasher()
        context = cls.Context(0, None, False)
        # Iterate over image-file names. One file at a time, compute per-file
        # hash and hamming distance to previous.
        if args.filesOnStdin:
            if args.filenames:
                parser.print_help()
                exit(1)
            try:
                lno = 0
                for filename in sys.stdin:
                    lno += 1
                    context.numPDQHash += 1
                    cls.processFile(
                        pdqHasher,
                        filename.strip(),
                        args.doPDQ,
                        args.doPDQDih,
                        args.doPDQDihAcross,
                        args.doDetailedOutput,
                        args.doTimings,
                        args.keepGoingAfterErrors,
                        context,
                    )
                    sys.stdout.flush()
                exit(0)
            except IOError:
                sys.stderr.write(
                    "{}: couldn't read line {} \n".format(cls.PROGNAME, lno)
                )
                exit(1)

        for filename in args.filenames:
            context.numPDQHash += 1
            cls.processFile(
                pdqHasher,
                filename,
                args.doPDQ,
                args.doPDQDih,
                args.doPDQDihAcross,
                args.doDetailedOutput,
                args.doTimings,
                args.keepGoingAfterErrors,
                context,
            )
            sys.stdout.flush()
        if context.hadError:
            exit(1)

    @classmethod
    def processFile(
        cls,
        pdqHasher,
        filename,
        doPDQHash,
        doPDQDih,
        doPDQDihAcross,
        doDetailedOutput,
        doTimings,
        keepGoingAfterErrors,
        context,
    ):
        hash = None
        hashAndQuality = None
        dihedralBag = None
        quality = int()
        norm = int()
        delta = int()
        hashingMetadata = PDQHasher.HashingMetadata()
        if doPDQHash:
            try:
                hashAndQuality = pdqHasher.fromFile(filename, hashingMetadata)
            except IOError as e:
                context.hadError = True
                sys.stderr.write(
                    "{}: could not read image file {}, Error {}\n".format(
                        cls.PROGNAME, filename, e
                    )
                )
                if keepGoingAfterErrors:
                    return
                else:
                    exit(1)
            hash = hashAndQuality.getHash()
            quality = hashAndQuality.getQuality()
            norm = hash.hammingNorm()

            if context.numPDQHash == 1:
                delta = 0
            else:
                delta = hash.hammingDistance(context.pdqHashPrev)

            if not doDetailedOutput:
                print("{},{},{}".format(hash, quality, filename))
            else:
                output = "hash={},norm={},delta={},quality={}".format(
                    hash, norm, delta, quality
                )
                if doTimings:
                    output += ",dims={},readSeconds={:.6f},hashSeconds={:.6f}".format(
                        hashingMetadata.imageHeightTimesWidth,
                        hashingMetadata.readSeconds,
                        hashingMetadata.hashSeconds,
                    )
                output += ",filename={}".format(filename)
                print(output)
            context.pdqHashPrev = hash
        if doPDQDih:
            try:
                dihedralBag = pdqHasher.dihedralFromFile(
                    filename, hashingMetadata, PDQHasher.PDQ_DO_DIH_ALL
                )
            except IOError as e:
                context.hadError = True
                sys.stderr.write(
                    "%s: could not read image file %s.\n".format(cls.PROGNAME, filename)
                )
                if keepGoingAfterErrors:
                    return
                else:
                    exit(1)
            if not doDetailedOutput:
                if doPDQDihAcross:
                    print(
                        "{},{},{},{},{},{},{},{},{},{}".format(
                            dihedralBag.hash,
                            dihedralBag.hashRotate90,
                            dihedralBag.hashRotate180,
                            dihedralBag.hashRotate270,
                            dihedralBag.hashFlipX,
                            dihedralBag.hashFlipY,
                            dihedralBag.hashFlipPlus1,
                            dihedralBag.hashFlipMinus1,
                            dihedralBag.quality,
                            filename,
                        )
                    )
                else:
                    bquality = dihedralBag.quality
                    print("{},{},{}".format(dihedralBag.hash, bquality, filename))
                    print(
                        "{},{},{}".format(dihedralBag.hashRotate90, bquality, filename)
                    )
                    print(
                        "{},{},{}".format(dihedralBag.hashRotate180, bquality, filename)
                    )
                    print(
                        "{},{},{}".format(dihedralBag.hashRotate270, bquality, filename)
                    )
                    print("{},{},{}".format(dihedralBag.hashFlipX, bquality, filename))
                    print("{},{},{}".format(dihedralBag.hashFlipY, bquality, filename))
                    print(
                        "{},{},{}".format(dihedralBag.hashFlipPlus1, bquality, filename)
                    )
                    print(
                        "{},{},{}".format(
                            dihedralBag.hashFlipMinus1, bquality, filename
                        )
                    )
            else:
                if doPDQDihAcross:
                    output = "hash={},quality={}".format(
                        dihedralBag.hash, dihedralBag.quality
                    )
                    if doTimings:
                        output += (
                            ",dims={},readSeconds={:.6f},hashSeconds={:.6f}".format(
                                hashingMetadata.imageHeightTimesWidth,
                                hashingMetadata.readSeconds,
                                hashingMetadata.hashSeconds,
                            )
                        )
                    output += ",orig={},rot90={},rot180={},,rot270={},flipx={},flipy={},flipp={},flipm={},filename={}".format(
                        dihedralBag.hash,
                        dihedralBag.hashRotate90,
                        dihedralBag.hashRotate180,
                        dihedralBag.hashRotate270,
                        dihedralBag.hashFlipX,
                        dihedralBag.hashFlipY,
                        dihedralBag.hashFlipPlus1,
                        dihedralBag.hashFlipMinus1,
                        filename,
                    )
                    print(output)
                else:
                    output = "hash={},quality={}".format(
                        dihedralBag.hash, dihedralBag.quality
                    )
                    if doTimings:
                        output += (
                            ",dims={},readSeconds={:.6f},hashSeconds={:.6f}".format(
                                hashingMetadata.imageHeightTimesWidth,
                                hashingMetadata.readSeconds,
                                hashingMetadata.hashSeconds,
                            )
                        )
                    output += ",filename={}".format(filename)
                    print(output)
                    print(
                        "hash={},xform=orig,filename={}".format(
                            dihedralBag.hash, filename
                        )
                    )
                    print(
                        "hash={},xform=rot90,filename={}".format(
                            dihedralBag.hashRotate90, filename
                        )
                    )
                    print(
                        "hash={},xform=rot180,filename={}".format(
                            dihedralBag.hashRotate180, filename
                        )
                    )
                    print(
                        "hash={},xform=rot270,filename={}".format(
                            dihedralBag.hashRotate270, filename
                        )
                    )
                    print(
                        "hash={},xform=flipx,filename={}".format(
                            dihedralBag.hashFlipX, filename
                        )
                    )
                    print(
                        "hash={},xform=flipy,filename={}".format(
                            dihedralBag.hashFlipY, filename
                        )
                    )
                    print(
                        "hash={},xform=flipp,filename={}".format(
                            dihedralBag.hashFlipPlus1, filename
                        )
                    )
                    print(
                        "hash={},xform=flipm,filename={}".format(
                            dihedralBag.hashFlipMinus1, filename
                        )
                    )
            context.pdqHashPrev = dihedralBag.hash.clone()


if __name__ == "__main__":
    PDQPhotoHasherTool.main(sys.argv)
