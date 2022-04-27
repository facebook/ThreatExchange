# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import argparse
import logging
import pathlib
import sys
import tempfile
import shutil

from threatexchange.cli.exceptions import CommandError

"""
Common helpers for the CLI

Could have been called "common.py"
"""


class FlexFilesInputAction(argparse.Action):
    """
    Takes filenames (or others) and stores path.Path objects.

    An action to support the following argument inputs:

    By default assumes filename
    If `--` is passed in, the remainder is interpreted as text
    If empty, reads from stidin.

    Use with nargs=argparse.REMAINDER for best results, which gives you:

    $ echo "Some text" > file.txt; cmd file.txt
    $ echo "Some text" | cmd
    $ cmd -- Some text

    All producing the same result.
    """

    def __call__(self, _parser, namespace, values, _option_string=None):
        args = list(values)
        if not args:  # If inputs, assume stdin
            with tempfile.NamedTemporaryFile("wb", delete=False) as tmp:
                logging.debug("Writing stdin to %s", tmp.name)
                shutil.copyfileobj(sys.stdin.buffer, tmp)
            args.append(tmp.name)
        # We have special behavior for -- but argparse sometimes eats it during parsing...
        if "--" in sys.argv and sys.argv[-len(args) - 1] == "--":
            args.insert(0, "--")
        ret = []
        for i, filename in enumerate(args):
            if filename.strip() == "--":
                # We could also just open this as a series of streams and seek() them
                with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
                    logging.debug("Writing -- to %s", tmp.name)
                    tmp.write(" ".join(args[i + 1 :]))
                ret.append(pathlib.Path(tmp.name))
                break
            path = pathlib.Path(filename)
            if not path.is_file():
                raise CommandError(f"No such file {path}", 2)
            ret.append(path)
        setattr(namespace, self.dest, ret)
