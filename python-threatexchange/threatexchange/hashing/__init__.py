# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
import warnings

try:
    from threatexchange.hashing.pdq_faiss_matcher import (
        PDQHashIndex,
        PDQFlatHashIndex,
        PDQMultiHashIndex,
        BITS_IN_PDQ,
    )
except:
    warnings.warn(
        "pdq matchers require faiss to be installed; install threatexchange with the [faiss] extra to use them",
        category=ImportWarning,
    )
