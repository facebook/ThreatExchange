# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
import warnings

try:
    from pytx3.hashing.pdq_faiss_matcher import (
        PDQHashIndex,
        PDQFlatHashIndex,
        PDQMultiHashIndex,
        BITS_IN_PDQ,
    )
except:
    warnings.warn(
        "pdq matchers require faiss to be installed; install pytx3 with the [faiss] extra to use them",
        category=ImportWarning,
    )
