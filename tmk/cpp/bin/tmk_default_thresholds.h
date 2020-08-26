// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

#ifndef TMK_DEFAULT_THRESHOLDS_H
#define TMK_DEFAULT_THRESHOLDS_H

// Note that thresholds depend on choice of frame-feature algorithm. The
// following have been validated for TMK+PDQF
// (https://fb.quip.com/CUwhAbCpZGQw).
#define DEFAULT_LEVEL_1_THRESHOLD 0.7
#define DEFAULT_LEVEL_2_THRESHOLD 0.7

// These are the minimum-possible values. They result in the most expensive
// possible scan through input video data.
#define FULL_DEFAULT_LEVEL_1_THRESHOLD -1.0
#define FULL_DEFAULT_LEVEL_2_THRESHOLD 0.0

#endif // TMK_DEFAULT_THRESHOLDS_H
