# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import json
import pathlib
import dacite
import dataclasses
from enum import Enum
import typing as t

T = t.TypeVar("T")


def dataclass_dump_file(path: pathlib.Path, obj) -> None:
    with path.open("w") as fp:
        dataclass_dump(fp, obj)


def dataclass_dump(fp: t.IO[str], obj) -> None:
    json_dict = dataclasses.asdict(obj)
    # Sanity check - we want to make sure it will also come out the other end
    # And this will wrong-type error if it can't
    dataclass_load_dict(json_dict, obj.__class__)
    return json.dump(json_dict, fp, indent=2, default=_json_set_default)


def dataclass_load_file(
    path: pathlib.Path, cls: t.Type[T], *, default: t.Optional[T] = None
) -> T:
    if not path.is_file():
        if default is not None:
            return default
        raise ValueError(f"cannot load dataclass: no such file {path}")
    with path.open("r") as fp:
        return dataclass_load(fp, cls)


def dataclass_load(fp: t.IO[str], cls: t.Type[T]) -> T:
    json_dict = json.load(fp)
    return dataclass_load_dict(json_dict, cls)


def dataclass_load_dict(json_dict: t.Dict[str, t.Any], cls: t.Type[T]) -> T:
    return dacite.from_dict(
        data_class=cls,
        data=json_dict,
        config=dacite.Config(cast=[Enum, set]),
    )


def _json_set_default(obj):
    if isinstance(obj, set):
        return list(obj)
    raise TypeError