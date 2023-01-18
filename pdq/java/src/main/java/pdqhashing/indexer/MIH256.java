// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

package pdqhashing.indexer;

import pdqhashing.types.Hash256;
import pdqhashing.types.Hash256AndMetadata;
import pdqhashing.types.MIHDimensionExceededException;

import java.io.PrintStream;
import java.util.BitSet;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.Vector;

/**
 * See hashing/pdq/README-MIH.md in this repo for important information
 * regarding parameter selection and performance.
 */
public class MIH256<Metadata> {
  private static final int MIH_MAX_D = 63;
  private static final int MIH_MAX_SLOTWISE_D = 3;

  // ----------------------------------------------------------------
  // MIH data:

  // 1. Array of all hashes+metadata in the index.
  //Vector<>
  private Vector<Hash256AndMetadata<Metadata>> _allHashesAndMetadatas;

  // 2. For each slot index i=0..15:
  //      For each of up to 65,536 possible slot values v at that index:
  //        Hashset of indices within the _allHashesAndMetadatas array of all hashes
  //        having slot value v at slot index i.
  private Vector<Map<Short, Vector<Integer>>> _slotValuesToIndices;

  // ----------------------------------------------------------------
  public MIH256() {
    _allHashesAndMetadatas = new Vector<Hash256AndMetadata<Metadata>>();
    _slotValuesToIndices = new Vector<Map<Short, Vector<Integer>>>();
    for (int i = 0; i < Hash256.HASH256_NUM_SLOTS; i++) {
      Map <Short, Vector<Integer>> element = new HashMap<Short, Vector<Integer>>();
      _slotValuesToIndices.add(element);
    }
  }

  public int size() {
    return _allHashesAndMetadatas.size();
  }

  // ---------------------------------------------------------------
  // BULK HASH INSERTION
  public void insertAll(Vector<Hash256AndMetadata<Metadata>> pairs) {
    for (Hash256AndMetadata<Metadata> pair : pairs) {
      insert(pair.hash, pair.metadata);
    }
  }

  // ---------------------------------------------------------------
  // HASH INSERTION
  public void insert(Hash256 hash, Metadata metadata) {
    int sizeBeforeInsert = _allHashesAndMetadatas.size();

    for (int i = 0; i < Hash256.HASH256_NUM_SLOTS; i++) {
      short slotValue = hash.w[i];
      Map<Short,Vector<Integer>> indicesForSlotValue = _slotValuesToIndices.get(i);
      if (!indicesForSlotValue.containsKey(slotValue)) {
        indicesForSlotValue.put(slotValue, new Vector<Integer>());
      }
      int index = sizeBeforeInsert;
      indicesForSlotValue.get(slotValue).add(index);
    }

    _allHashesAndMetadatas.add(new Hash256AndMetadata<Metadata>(hash, metadata));
  }

  // ----------------------------------------------------------------
  // HASH QUERY FOR ALL MATCHES
  //
  // MIH query algorithm:
  // Given needle hash n
  // For each slot index i:
  //   Get slot value v of n at index i
  //     Find the array indices of hashes in the MIH whose i'th slot value
  //     is within slotwise distance of v. Do this by finding all the
  //     nearest-neighbor values w of v and finding the indices of all
  //     hashes having value w at slot index i.

  public void queryAll(
    Hash256 needle,
    int d,
    Vector<Hash256AndMetadata<Metadata>> matches)
      throws MIHDimensionExceededException
  {
    Set<Integer> indices = new HashSet<Integer>();
    int slotwise_d = d / 16; // Floor of d/16; see comments at top of file.

    // Find candidates
    for (int i = 0; i < Hash256.HASH256_NUM_SLOTS; i++) {
      short slotValue = needle.w[i];
      Map<Short,Vector<Integer>> indicesForSlotValue = _slotValuesToIndices.get(i);
      switch(slotwise_d) {
      case 0: queryAll0(slotValue, indicesForSlotValue, indices); break;
      case 1: queryAll1(slotValue, indicesForSlotValue, indices); break;
      case 2: queryAll2(slotValue, indicesForSlotValue, indices); break;
      case 3: queryAll3(slotValue, indicesForSlotValue, indices); break;
      default:
        throw new MIHDimensionExceededException(
          String.format(
            "PDQ MIH queryAll: distance threshold %d out of bounds 0..%d. Please use linear search.",
              d, MIH_MAX_D
          )
        );
      }
    }

    // Prune candidates
    for (Integer index : indices) {
      Hash256AndMetadata<Metadata> pair = _allHashesAndMetadatas.get(index);
      Hash256 hash = pair.hash;
      Metadata metadata = pair.metadata;
      if (hash.hammingDistance(needle) <= d) {
        matches.add(pair); // Not: not cloned, for safe of performance
      }
    }
  }

  private void queryAllNeighborAux(
    short neighbor,
    Map<Short,Vector<Integer>> indicesForSlotValue,
    Set<Integer> indices
  ) {
    if (indicesForSlotValue.containsKey(neighbor)) {
      for (Integer index : indicesForSlotValue.get(neighbor)) {
        indices.add(index);
      }
    }
  }

  private void queryAll0(
    short neighbor0,
    Map<Short,Vector<Integer>> indicesForSlotValue,
    Set<Integer> indices
  ) {
    queryAllNeighborAux(neighbor0, indicesForSlotValue, indices);
  }

  private void queryAll1(
    short neighbor0,
    Map<Short,Vector<Integer>> indicesForSlotValue,
    Set<Integer> indices
  ) {
    queryAllNeighborAux(neighbor0, indicesForSlotValue, indices);
    for (int i1 = 0; i1 < 16; i1++) {
      int neighbor1 = neighbor0 ^ (1 << i1);
      queryAllNeighborAux((short)neighbor1, indicesForSlotValue, indices);
    }
  }

  private void queryAll2(
    short neighbor0,
    Map<Short,Vector<Integer>> indicesForSlotValue,
    Set<Integer> indices
  ) {
    queryAllNeighborAux(neighbor0, indicesForSlotValue, indices);
    for (int i1 = 0; i1 < 16; i1++) {
      int neighbor1 = neighbor0 ^ (1 << i1);
      queryAllNeighborAux((short)neighbor1, indicesForSlotValue, indices);
      for (int i2 = i1+1; i2 < 16; i2++) {
        int neighbor2 = neighbor1 ^ (1 << i2);
        queryAllNeighborAux((short)neighbor2, indicesForSlotValue, indices);
      }
    }
  }

  private void queryAll3(
    short neighbor0,
    Map<Short,Vector<Integer>> indicesForSlotValue,
    Set<Integer> indices
  ) {
    queryAllNeighborAux(neighbor0, indicesForSlotValue, indices);
    for (int i1 = 0; i1 < 16; i1++) {
      int neighbor1 = neighbor0 ^ (1 << i1);
      queryAllNeighborAux((short)neighbor1, indicesForSlotValue, indices);
      for (int i2 = i1+1; i2 < 16; i2++) {
        int neighbor2 = neighbor1 ^ (1 << i2);
        queryAllNeighborAux((short)neighbor2, indicesForSlotValue, indices);
        for (int i3 = i2+1; i3 < 16; i3++) {
          int neighbor3 = neighbor2 ^ (1 << i3);
          queryAllNeighborAux((short)neighbor3, indicesForSlotValue, indices);
        }
      }
    }
  }

  // ----------------------------------------------------------------
  // HASH QUERY FOR ANY MATCHES

  public Hash256AndMetadata<Metadata> queryAny(
    Hash256 needle,
    int d)
      throws MIHDimensionExceededException
  {
    BitSet indicesChecked = new BitSet(_allHashesAndMetadatas.size());
    int slotwise_d = d / 16; // Floor of d/16; see comments at top of file.

    switch(slotwise_d) {

    case 0:
      for (int i = 0; i < Hash256.HASH256_NUM_SLOTS; i++) {
        short slotValue = needle.w[i];
        Map<Short,Vector<Integer>> indicesForSlotValue = _slotValuesToIndices.get(i);
        Hash256AndMetadata<Metadata> pair = queryAny0(slotValue, needle, d, indicesForSlotValue, indicesChecked);
        if (pair != null) {
          return pair;
        }
      }
      return null;

    case 1:
      for (int i = 0; i < Hash256.HASH256_NUM_SLOTS; i++) {
        short slotValue = needle.w[i];
        Map<Short,Vector<Integer>> indicesForSlotValue = _slotValuesToIndices.get(i);
        Hash256AndMetadata<Metadata> pair = queryAny1(slotValue, needle, d, indicesForSlotValue, indicesChecked);
        if (pair != null) {
          return pair;
        }
      }
      return null;

    case 2:
      for (int i = 0; i < Hash256.HASH256_NUM_SLOTS; i++) {
        short slotValue = needle.w[i];
        Map<Short,Vector<Integer>> indicesForSlotValue = _slotValuesToIndices.get(i);
        Hash256AndMetadata<Metadata> pair = queryAny2(slotValue, needle, d, indicesForSlotValue, indicesChecked);
        if (pair != null) {
          return pair;
        }
      }
      return null;

    case 3:
      for (int i = 0; i < Hash256.HASH256_NUM_SLOTS; i++) {
        short slotValue = needle.w[i];
        Map<Short,Vector<Integer>> indicesForSlotValue = _slotValuesToIndices.get(i);
        Hash256AndMetadata<Metadata> pair = queryAny3(slotValue, needle, d, indicesForSlotValue, indicesChecked);
        if (pair != null) {
          return pair;
        }
      }
      return null;

    default:
      throw new MIHDimensionExceededException(
        String.format(
          "PDQ MIH queryAny: distance threshold %d out of bounds 0..%d. Please use linear search.",
            d, MIH_MAX_D
        )
      );
    }
  }

  private Hash256AndMetadata<Metadata> queryAnyNeighborAux(
    short neighbor,
    Hash256 needle,
    int d,
    Map<Short,Vector<Integer>> indicesForSlotValue,
    BitSet indicesChecked
  ) {
    Vector<Integer> v = indicesForSlotValue.get(neighbor);
    if (v != null) {
      for (Integer index : v) {
        Hash256AndMetadata<Metadata> pair = _allHashesAndMetadatas.get(index);
        if (!indicesChecked.get(index)) {
          if (pair.hash.hammingDistanceLE(needle, d)) {
           return pair;
          }
        }
        indicesChecked.set(index);
      }
    }
    return null;
  }

  private Hash256AndMetadata<Metadata> queryAny0(
    short neighbor0,
    Hash256 needle,
    int d,
    Map<Short,Vector<Integer>> indicesForSlotValue,
    BitSet indicesChecked
  ) {
    Hash256AndMetadata<Metadata> pair = queryAnyNeighborAux(neighbor0, needle, d, indicesForSlotValue, indicesChecked);
    if (pair != null) {
      return pair;
    }
    return null;
  }

  private Hash256AndMetadata<Metadata> queryAny1(
    short neighbor0,
    Hash256 needle,
    int d,
    Map<Short,Vector<Integer>> indicesForSlotValue,
    BitSet indicesChecked
  ) {
    Hash256AndMetadata<Metadata> pair = queryAnyNeighborAux(neighbor0, needle, d, indicesForSlotValue, indicesChecked);
    if (pair != null) {
      return pair;
    }
    for (int i1 = 0; i1 < 16; i1++) {
      int neighbor1 = neighbor0 ^ (1 << i1);
      pair = queryAnyNeighborAux((short)neighbor1, needle, d, indicesForSlotValue, indicesChecked);
      if (pair != null) {
        return pair;
      }
    }
    return null;
  }

  private Hash256AndMetadata<Metadata> queryAny2(
    short neighbor0,
    Hash256 needle,
    int d,
    Map<Short,Vector<Integer>> indicesForSlotValue,
    BitSet indicesChecked
  ) {
    Hash256AndMetadata<Metadata> pair = queryAnyNeighborAux(neighbor0, needle, d, indicesForSlotValue, indicesChecked);
    if (pair != null) {
      return pair;
    }
    for (int i1 = 0; i1 < 16; i1++) {
      int neighbor1 = neighbor0 ^ (1 << i1);
      pair = queryAnyNeighborAux((short)neighbor1, needle, d, indicesForSlotValue, indicesChecked);
      if (pair != null) {
        return pair;
      }
      for (int i2 = i1+1; i2 < 16; i2++) {
        int neighbor2 = neighbor1 ^ (1 << i2);
        pair = queryAnyNeighborAux((short)neighbor2, needle, d, indicesForSlotValue, indicesChecked);
        if (pair != null) {
          return pair;
        }
      }
    }
    return null;
  }

  private Hash256AndMetadata<Metadata> queryAny3(
    short neighbor0,
    Hash256 needle,
    int d,
    Map<Short,Vector<Integer>> indicesForSlotValue,
    BitSet indicesChecked
  ) {
    Hash256AndMetadata<Metadata> pair = queryAnyNeighborAux(neighbor0, needle, d, indicesForSlotValue, indicesChecked);
    if (pair != null) {
      return pair;
    }
    for (int i1 = 0; i1 < 16; i1++) {
      int neighbor1 = neighbor0 ^ (1 << i1);
      pair =queryAnyNeighborAux((short)neighbor1, needle, d, indicesForSlotValue, indicesChecked);
      if (pair != null) {
        return pair;
      }
      for (int i2 = i1+1; i2 < 16; i2++) {
        int neighbor2 = neighbor1 ^ (1 << i2);
        pair = queryAnyNeighborAux((short)neighbor2, needle, d, indicesForSlotValue, indicesChecked);
        if (pair != null) {
          return pair;
        }
        for (int i3 = i2+1; i3 < 16; i3++) {
          int neighbor3 = neighbor2 ^ (1 << i3);
          pair = queryAnyNeighborAux((short)neighbor3, needle, d, indicesForSlotValue, indicesChecked);
          if (pair != null) {
            return pair;
          }
        }
      }
    }
    return null;
  }

  // ----------------------------------------------------------------
  // LINEAR SEARCH
  public void bruteForceQueryAll(
    Hash256 needle,
    int d,
    Vector<Hash256AndMetadata<Metadata>> matches
  ) {
    for (Hash256AndMetadata<Metadata> pair : _allHashesAndMetadatas) {
      if (pair.hash.hammingDistance(needle) <= d) {
        matches.add(pair);
      }
    }
  }

  // ----------------------------------------------------------------
  // LINEAR SEARCH
  public Hash256AndMetadata<Metadata> bruteForceQueryAny(
    Hash256 needle,
    int d
  ) {
    for (Hash256AndMetadata<Metadata> pair : _allHashesAndMetadatas) {
      if (pair.hash.hammingDistanceLE(needle, d)) {
        return pair;
      }
    }
    return null;
  }

  // ----------------------------------------------------------------
  // OPS/REGRESSION ROUTINE
  public void dump(PrintStream o) {
    o.printf("ALL HASHES:\n");
    for (Hash256AndMetadata<Metadata> pair : _allHashesAndMetadatas) {
      o.printf("%s\n", pair.hash.toString());
      o.flush();
    }
    o.printf("MULTI-INDICES:\n");
    for (int i = 0; i < Hash256.HASH256_NUM_SLOTS; i++) {
      o.printf("\n");
      o.printf("--------------- slot_index=%d\n", i);
      Map<Short, Vector<Integer>> ati = _slotValuesToIndices.get(i);
      for (Map.Entry<Short, Vector<Integer>> entry : ati.entrySet()) {
        Short slotValue = entry.getKey();
        Vector<Integer> indices = entry.getValue();
        o.printf("slot_value=%04x\n", (int)slotValue);
        for (Integer index : indices) {
          o.printf("  %d\n", index);
          o.flush();
        }
        o.flush();
      }
      o.flush();
    }
  }
}
