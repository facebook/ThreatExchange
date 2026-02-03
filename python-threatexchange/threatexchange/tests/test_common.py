# Copyright (c) Meta Platforms, Inc. and affiliates.

import threatexchange.common


def test_camel_case_to_underscore():
    assert threatexchange.common.camel_case_to_underscore("AbcXyz") == "abc_xyz"
