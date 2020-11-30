# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
import warnings

from pytx3.hashing.pdq_utils import BITS_IN_PDQ

try:
    from pytx3.hashing.pdq_faiss_matcher import (
        PDQHashIndex,
        PDQFlatHashIndex,
        PDQMultiHashIndex,
    )
except:
    warnings.warn(
        "pdq matchers require faiss to be installed; install pytx3 with the [faiss] extra to use them",
        category=ImportWarning,
    )
