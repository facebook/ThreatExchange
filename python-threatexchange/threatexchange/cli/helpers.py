# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import argparse
import logging
import pathlib
import sys
import tempfile
import shutil
import typing as t

import requests

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
        args: t.List[str] = list(values)
        if not args:
            raise argparse.ArgumentError(self, "this argument is required")
        # We have special behavior for -- but argparse sometimes eats it during parsing...
        if "--" in sys.argv and sys.argv[-len(args) - 1] == "--":
            args.insert(0, "--")
        ret = []
        for i, filename in enumerate(args):
            if filename.strip() == "-":
                with tempfile.NamedTemporaryFile("wb", delete=False) as tmp:
                    logging.debug("Writing stdin to %s", tmp.name)
                    shutil.copyfileobj(sys.stdin.buffer, tmp)
                filename = tmp.name
            elif filename.strip() == "--":
                # We could also just open this as a series of streams and seek() them
                with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
                    logging.debug("Writing -- to %s", tmp.name)
                    tmp.write(" ".join(args[i + 1 :]))
                filename = tmp.name
                ret.append(pathlib.Path(tmp.name))
                break
            elif filename.startswith(("http://", "https://")):
                resp = requests.get(filename, allow_redirects=True)
                resp.raise_for_status()
                with tempfile.NamedTemporaryFile("wb", delete=False) as tmp:
                    logging.debug("Writing -- to %s", tmp.name)
                    tmp.write(resp.content)
                filename = pathlib.Path(tmp.name)
            path = pathlib.Path(filename)
            if not path.is_file():
                raise argparse.ArgumentError(self, f"no such file {path}")
            ret.append(path)
        setattr(namespace, self.dest, ret)
