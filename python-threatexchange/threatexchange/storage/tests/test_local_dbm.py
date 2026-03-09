# Copyright (c) Meta Platforms, Inc. and affiliates.

import pathlib

from threatexchange.storage import interfaces as iface
from threatexchange.storage import local_dbm


def test_signal_type(tmpdir: pathlib.Path):
    storage: iface.ISignalTypeConfigStore = local_dbm.DBMStore(pathlib.Path(tmpdir))

    # Get with unset values
    cfgs = storage.get_signal_type_configs()
    assert set(cfgs) == {"pdq", "video_md5"}
    for val in cfgs.values():
        assert val.enabled_ratio == 1.0

    # Override one
    storage.create_or_update_signal_type_override("pdq", 0.5)
    cfgs = storage.get_signal_type_configs()
    assert set(cfgs) == {"pdq", "video_md5"}
    assert cfgs["pdq"].enabled_ratio == 0.5
    assert cfgs["video_md5"].enabled_ratio == 1.0


def test_content_type(tmpdir: pathlib.Path):
    storage = local_dbm.DBMStore(pathlib.Path(tmpdir))

    # Get with unset values — all enabled by default
    cfgs = storage.get_content_type_configs()
    assert set(cfgs) == {"photo", "video"}
    for val in cfgs.values():
        assert val.enabled is True

    # Override one
    storage._create_or_update_content_type_override("photo", False)
    cfgs = storage.get_content_type_configs()
    assert set(cfgs) == {"photo", "video"}
    assert cfgs["photo"].enabled is False
    assert cfgs["video"].enabled is True
