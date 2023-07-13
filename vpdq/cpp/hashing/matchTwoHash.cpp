// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#include <iostream>

#include <pdq/cpp/io/hashio.h>
#include <vpdq/cpp/hashing/vpdqHashType.h>
#include <vpdq/cpp/io/vpdqio.h>

namespace facebook {
namespace vpdq {
namespace hashing {
bool matchTwoHashBrute(
    std::vector<vpdq::hashing::vpdqFeature> qHashes,
    std::vector<vpdq::hashing::vpdqFeature> tHashes,
    int distanceTolerance,
    int qualityTolerance,
    double& qMatch,
    double& tMatch,
    const bool verbose) {
  // Filter low quality hashes for query
  std::vector<vpdq::hashing::vpdqFeature> queryFiltered;
  for (const auto& qHash : qHashes) {
    if (qHash.quality >= qualityTolerance) {
      queryFiltered.push_back(qHash);
    } else if (verbose) {
      auto i = &qHash - &qHashes[0];
      std::cout << "Skipping Line " << i
                << " Skipping Query Hash: " << qHash.pdqHash.format()
                << ", because of low quality Query Hash: " << qHash.quality
                << std::endl;
    }
  }

  // Filter low quality hashes for target
  std::vector<vpdq::hashing::vpdqFeature> targetFiltered;
  for (const auto& tHash : tHashes) {
    if (tHash.quality >= qualityTolerance) {
      targetFiltered.push_back(tHash);
    } else if (verbose) {
      auto j = &tHash - &tHashes[0];
      std::cout << "Skipping Line " << j
                << " Skipping Target Hash: " << tHash.pdqHash.format()
                << ", because of low quality Target Hash: " << tHash.quality
                << std::endl;
    }
  }

  // Get matches for query in target
  unsigned int qMatchCnt = 0;
  for (const auto& qHash : queryFiltered) {
    for (const auto& tHash : targetFiltered) {
      if (qHash.pdqHash.hammingDistance(tHash.pdqHash) < distanceTolerance) {
        qMatchCnt++;
        if (verbose) {
          std::cout << "Query Hash: " << qHash.pdqHash.format()
                    << " Target Hash: " << tHash.pdqHash.format() << " match "
                    << std::endl;
        }
        break;
      }
    }
  }

  // Get matches for target in query
  unsigned int tMatchCnt = 0;
  for (const auto& tHash : targetFiltered) {
    for (const auto& qHash : queryFiltered) {
      if (tHash.pdqHash.hammingDistance(qHash.pdqHash) < distanceTolerance) {
        tMatchCnt++;
        if (verbose) {
          std::cout << "Query Hash: " << qHash.pdqHash.format()
                    << " Target Hash: " << tHash.pdqHash.format() << " match "
                    << std::endl;
        }
        break;
      }
    }
  }

  qMatch = (qMatchCnt * 100.0) / queryFiltered.size();
  tMatch = (tMatchCnt * 100.0) / targetFiltered.size();
  return true;
}
} // namespace hashing
} // namespace vpdq
} // namespace facebook
