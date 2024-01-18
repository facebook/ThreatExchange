// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#ifndef VPDQHASHTYPE_H
#define VPDQHASHTYPE_H

#include <pdq/cpp/common/pdqhashtypes.h>

using namespace std;

namespace facebook {
namespace vpdq {
namespace hashing {

struct vpdqFeature {
  facebook::pdq::hashing::Hash256 pdqHash;
  int frameNumber;
  int quality;
  double timeStamp;
};

} // namespace hashing
} // namespace vpdq
} // namespace facebook

#endif // VPDQHASHTYPE_H
