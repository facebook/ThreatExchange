// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

#ifndef MIH_H
#define MIH_H

#include <pdq/cpp/common/pdqhashtypes.h>
#include <map>
#include <set>
#include <vector>

namespace facebook {
namespace pdq {
namespace index {

// ================================================================
// MUTUALLY-INDEXED HASHING FOR 256-BIT HASHES
//
// ----------------------------------------------------------------
// References:
// Mutually-indexed hashing by Norouzi et al. 2014:
// * https://www.cs.toronto.edu/~norouzi/research/papers/multi_index_hashing.pdf
// * https://norouzi.github.io/research/posters/mih_poster.pdf
// * This is a from-scratch source-code implementation based on the paper.
//
// ----------------------------------------------------------------
// Size constraints:
//
// 'Slots' are 16-bit words. Maximum distance we support for non-brute-force
// search is MIH_MAX_SLOTWISE_D.  This corresponds to max hashwise distance of
// MIH_MAX_D since that's the largest d such that floor(d/16) <=
// MIH_MAX_SLOTWISE_D.
//
// The reason, in turn, for this is the expense of finding all hamming-distance
// nearest neighbors. For more information please see hashing/pdq/README-MIH.md
// in this repo.
// ================================================================

const int MIH_MAX_D = 63;
const int MIH_MAX_SLOTWISE_D = 3;

// Implemented entirely within the header file since this is a template class.
template <typename Metadata>
class MIH256 {
 private:
  // ----------------------------------------------------------------
  // MIH data:

  // 1. Array of all hashes+metadata in the index.
  std::vector<std::pair<facebook::pdq::hashing::Hash256, Metadata>> _allHashes;

  // 2. For each slot index i=0..15:
  //      For each of up to 65,536 possible slot values v at that index:
  //        Hashset of indices within the _allHashes array of all hashes
  //        having slot value v at slot index i.
  std::vector<std::map<facebook::pdq::hashing::Hash16, std::vector<int>>>
      _slotValuesToIndices;

 public:
  // ----------------------------------------------------------------
  MIH256() : _slotValuesToIndices(facebook::pdq::hashing::HASH256_NUM_WORDS) {}

  // ----------------------------------------------------------------
  // Let STL do the work of freeing its containers.
  ~MIH256() {}

 private:
  // Disallow copying
  MIH256(const MIH256& /*that*/) {}
  void operator=(const facebook::pdq::hashing::Hash256& /*that*/) {}

 public:
  // ----------------------------------------------------------------
  int size() {
    return _allHashes.size();
  }

  std::vector<std::pair<facebook::pdq::hashing::Hash256,Metadata>> get() {
    return _allHashes;
  }

  // ---------------------------------------------------------------
  // BULK INSERTION
  void insertAll(
      const std::vector<std::pair<facebook::pdq::hashing::Hash256, Metadata>>&
          pairs) {
    for (auto it : pairs) {
      insert(it.first, it.second);
    }
  }

  // ---------------------------------------------------------------
  // HASH INSERTION
  void insert(const facebook::pdq::hashing::Hash256& hash, Metadata metadata) {
    int sizeBeforeInsert = _allHashes.size();

    for (int i = 0; i < facebook::pdq::hashing::HASH256_NUM_WORDS; i++) {
      _slotValuesToIndices[i][hash.w[i]].push_back(sizeBeforeInsert);
    }

    _allHashes.push_back(std::make_pair(hash, metadata));
  }

  // ----------------------------------------------------------------
  void queryAllNeighborAux(
      facebook::pdq::hashing::Hash16 neighbor,
      const std::map<facebook::pdq::hashing::Hash16, std::vector<int>>&
          indicesForSlotValue,
      std::set<int>& indices) const {
    const auto found = indicesForSlotValue.find(neighbor);
    if (found != indicesForSlotValue.end()) {
      indices.insert(found->second.begin(), found->second.end());
    }
  }

  void queryAll0(
      facebook::pdq::hashing::Hash16 neighbor0,
      const std::map<facebook::pdq::hashing::Hash16, std::vector<int>>&
          indicesForSlotValue,
      std::set<int>& indices) const {
    queryAllNeighborAux(neighbor0, indicesForSlotValue, indices);
  }

  void queryAll1(
      facebook::pdq::hashing::Hash16 neighbor0,
      const std::map<facebook::pdq::hashing::Hash16, std::vector<int>>&
          indicesForSlotValue,
      std::set<int>& indices) const {
    queryAllNeighborAux(neighbor0, indicesForSlotValue, indices);
    for (int i1 = 0; i1 < 16; i1++) {
      facebook::pdq::hashing::Hash16 neighbor1 = neighbor0 ^ (1 << i1);
      queryAllNeighborAux(neighbor1, indicesForSlotValue, indices);
    }
  }

  void queryAll2(
      facebook::pdq::hashing::Hash16 neighbor0,
      const std::map<facebook::pdq::hashing::Hash16, std::vector<int>>&
          indicesForSlotValue,
      std::set<int>& indices) const {
    queryAllNeighborAux(neighbor0, indicesForSlotValue, indices);
    for (int i1 = 0; i1 < 16; i1++) {
      facebook::pdq::hashing::Hash16 neighbor1 = neighbor0 ^ (1 << i1);
      queryAllNeighborAux(neighbor1, indicesForSlotValue, indices);
      for (int i2 = i1 + 1; i2 < 16; i2++) {
        facebook::pdq::hashing::Hash16 neighbor2 = neighbor1 ^ (1 << i2);
        queryAllNeighborAux(neighbor2, indicesForSlotValue, indices);
      }
    }
  }

  void queryAll3(
      facebook::pdq::hashing::Hash16 neighbor0,
      const std::map<facebook::pdq::hashing::Hash16, std::vector<int>>&
          indicesForSlotValue,
      std::set<int>& indices) const {
    queryAllNeighborAux(neighbor0, indicesForSlotValue, indices);
    for (int i1 = 0; i1 < 16; i1++) {
      facebook::pdq::hashing::Hash16 neighbor1 = neighbor0 ^ (1 << i1);
      queryAllNeighborAux(neighbor1, indicesForSlotValue, indices);
      for (int i2 = i1 + 1; i2 < 16; i2++) {
        facebook::pdq::hashing::Hash16 neighbor2 = neighbor1 ^ (1 << i2);
        queryAllNeighborAux(neighbor2, indicesForSlotValue, indices);
        for (int i3 = i2 + 1; i3 < 16; i3++) {
          facebook::pdq::hashing::Hash16 neighbor3 = neighbor2 ^ (1 << i3);
          queryAllNeighborAux(neighbor3, indicesForSlotValue, indices);
        }
      }
    }
  }

  // ----------------------------------------------------------------
  // HASH QUERY
  //
  // MIH query algorithm:
  // Given needle hash n
  // For each slot index i:
  //   Get slot value v of n at index i
  //     Find the array indices of hashes in the MIH whose i'th slot value
  //     is within slotwise distance of v. Do this by finding all the
  //     nearest-neighbor values w of v and finding the indices of all
  //     hashes having value w at slot index i.

  void queryAll(
      const facebook::pdq::hashing::Hash256& needle,
      int d,
      std::vector<std::pair<facebook::pdq::hashing::Hash256, Metadata>>&
          matches) const {
    std::set<int> indices;
    // Floor of d/16; see comments at top of file:
    const int slotwise_d = d / 16;

    // Find candidates
    for (int i = 0; i < facebook::pdq::hashing::HASH256_NUM_WORDS; i++) {
      facebook::pdq::hashing::Hash16 slotValue = needle.w[i];
      const auto& indicesForSlotValue = _slotValuesToIndices[i];
      switch (slotwise_d) {
        case 0:
          queryAll0(slotValue, indicesForSlotValue, indices);
          break;
        case 1:
          queryAll1(slotValue, indicesForSlotValue, indices);
          break;
        case 2:
          queryAll2(slotValue, indicesForSlotValue, indices);
          break;
        case 3:
          queryAll3(slotValue, indicesForSlotValue, indices);
          break;
        default:
          throw std::runtime_error(
              "PDQ MIH queryAll: distance threshold out of bounds. "
              "Please use linear search.");
          break;
      }
    }

    // Prune candidates
    for (auto idx : indices) {
      const facebook::pdq::hashing::Hash256& hash = _allHashes[idx].first;
      const Metadata& metadata = _allHashes[idx].second;
      if (hash.hammingDistance(needle) <= d) {
        matches.push_back(std::make_pair(hash, metadata));
      }
    }
  }

  // ----------------------------------------------------------------
  // LINEAR SEARCH
  void bruteForceQueryAll(
      const facebook::pdq::hashing::Hash256& needle,
      int d,
      std::vector<std::pair<facebook::pdq::hashing::Hash256, Metadata>>&
          matches) const {
    for (auto it : _allHashes) {
      auto& hash = it.first;
      if (hash.hammingDistance(needle) <= d) {
        Metadata metadata = it.second;
        matches.push_back(std::make_pair(hash, metadata));
      }
    }
  }

  bool bruteForceQueryAny(
      const facebook::pdq::hashing::Hash256& needle,
      int d,
      facebook::pdq::hashing::Hash256& match) const {
    for (auto it : _allHashes) {
      auto& hash = it.first;
      if (hash.hammingDistanceLE(needle, d)) {
        match = hash;
        return true;
      }
    }
    return false;
  }

  // ----------------------------------------------------------------
  // OPS/REGRESSION ROUTINE
  void dump() {
    printf("ALL HASHES:\n");
    for (auto it : _allHashes) {
      facebook::pdq::hashing::Hash256& hash = it.first;
      printf("%s\n", hash.format().c_str());
      fflush(stdout);
    }
    printf("MULTI-INDICES:\n");
    for (int i = 0; i < facebook::pdq::hashing::HASH256_NUM_WORDS; i++) {
      printf("\n");
      printf("--------------- slot_index=%d\n", i);
      for (auto it1 : _slotValuesToIndices[i]) {
        facebook::pdq::hashing::Hash16 slotValue = it1.first;
        std::vector<int> indices = it1.second;
        printf("slot_value=%04hx\n", slotValue);
        for (auto it2 : indices) {
          printf("  %d\n", it2);
          fflush(stdout);
        }
        fflush(stdout);
      }
      fflush(stdout);
    }
  }

}; // end class MIH256

} // namespace index
} // namespace pdq
} // namespace facebook

#endif // MIH_H
