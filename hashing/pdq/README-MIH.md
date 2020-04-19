# Mutually indexed hashing for 256-bit hashes

## References

Mutually-indexed hashing by Norouzi et al. 2014:
* https://www.cs.toronto.edu/~norouzi/research/papers/multi_index_hashing.pdf
* https://norouzi.github.io/research/posters/mih_poster.pdf
This is a from-scratch source-code implementation based on the paper.

## Parameters

External parameters `n` and `d`; internal parameter m as follows, which
determines `k` and `s`.

* `n`: Hashes are `n` bits long: for PDQ, `n` is 256.

* `d`: We seek matches within Hamming distance `d`: for PDQ, anywhere from 0-63.

* `m` and `k`: We divide the hashes into `m` slots of length `k`: maybe 8 32-bit
  slots, 16 16-bit slots, 32 8-bit slots. (The final choice will be 16 16-bit
  slots, for reasons to be discussed below.)

* `s`: Slotwise distance threshold `s` is the floor of `n` / `m`.

## Key algorithmic insight

The key algorithmic insight of MIH is that if two hashes `u` and `v` have (hashwise)
Hamming distance <= `d`, they must have slotwise Hamming distance <= `s` in at
least one slot.

The proof is easy (by contradiction): if this weren't the case -- -- if `u` and `v`
differed by more than `s` in each slot -- they'd differ by more than `d`
overall.

This property allows us to look at substrings of hashes *closest* to another hash.

## Data structure

There is a **haystack** (database) of hashes, and a **needle** to be searched
for, within Hamming distance `d`.  The haystack hashes in the table are
placed into an array, with array indices from 0 up to the number of hashes.

In addition to the array, for each of the `m` slots, for each distinct value
ocurring in that slot, there is a hashmap from that slot value to the
array indices of all hashes in the table having that value at that slot.

Example: suppose we have haystack hashes as follows. Numbers across are slot
indices; numbers down are hash-array indices

```
      0    1    2    3    4    5    6    7    8    9   10   11   12   13   14   15
  0 e1b1 4c56 1c78 e381 f956 cc6c 6293 3a66 971c dda0 7a47 3dda 904b fdc8 cf24 62c9
  1 e9a1 ec53 4c68 eb89 f9d4 c94c 6698 3a66 971d 9de9 7ac7 3dde 944b fcc8 e725 62c9
  2 a191 4ad6 1878 e381 f9d2 dd4d 62d3 3a36 d71c c980 7245 3dda d042 fcc8 c724 62a9
  3 f1b1 4c36 1c59 6301 d9c6 9c2c e393 7e63 979c dda1 7247 2dda 940a fdd8 cf04 6a89
  4 e1b1 4e5e 5478 e305 f952 dcfc 63f3 3a66 911c d520 7ec6 3d9b 985b f5c8 df84 6acb
  5 f1ab 4cd7 1cf0 eb81 b9fe ca6d 6393 a266 971c d9a0 7e27 3ddb d24b fdc9 dc24 62e9
  6 e1b1 4e76 9478 e381 f95e dcac 6eb3 5e67 971e dda0 7ac7 6dd8 5002 edc8 ce24 62cb

  There are 16 hashmaps, for each of slots 0 through 15. The keyset for each is
  (as much as) all 2^16 possible slotwise values 0000 through ffff.

  At slot 0:
    e1b1 hashes to the index-list [0,4,6]
    e9a1 hashes to the index-list [1]
    a191 hashes to the index-list [2]
   ...
  At slot 1:
    4c56 hashes to the index-list [0]
    ec53 hashes to the index-list [1]
    4ad6 hashes to the index-list [2]
   ...

  and so on.
```

## Algorithm

Given a needle hash to be looked up, say

```
    e1b34e5e5478e385f952dcfc63f33a66911cd5207ec63d9b985bf5c8df846acb
```

then divide it into `m` `k`-bit slots. For example:

```
    e1b3 4e5e 5478 e385 f952 dcfc 63f3 3a66 911c d520 7ec6 3d9b 985b f5c8 df84 6acb
```

Lookups are two-step: (1) find candidate list; (2) prune candidate list.

* Find candidates:
  * For each needle slot, get the value at that slot: e.g. `e1b3` at slot 0.
  * Then enumerate all neighbors of that slot value within slotwise distance
    `s`. For example, if hashwise distance threshold is 30, then `s` = floor of
    30 / 16 = 1.  So slot value `e1b1` has 17 nearest neighbors within
    distance 1: itself at distance 0 (`e1b3`), and the 16 different single-bit
    flips (`61b3`, `a1b3`, `c1b3`, ..., `e1b1`, `e1b2`).
  * Consult the slot-0 hashmaps at all 17 slotwise neighbors and take the union
    of the indices they map to.
  * Now move to slot 1 and do the same, continuing to accumulate the union of
    the array indices for slot 1.
  * And so on for all the slots.

* Prune candidates:
  * Now we have a single hash-set of array indices for haystack hashes, all of
    which differ slotwise from the needle by <= `s` in at least one slot.
  * For each candidate hash, compute the full hashwise Hamming distance and
    retain only those which differ hashwise by <= `d` from the needle hash.

## Parameter selection

The values `n` for the hash width and `d` for the search threshold come from
the application. The choice of `k` -- the bit-width of the slots to divide the
hashes into -- determines `m` (how many slots) and `s` (slotwise distance
threshold).

The efficiency of MIH depends on a few things:

(1) Finding slotwise nearest neighbors (within `s`) for a given slot value must
be quick.

(2) The number of candidates found must be relatively small compared to
    the haystack size. (If not, the lookup is like a linear search.)

Using a database of 24 million PDQ hashes, experiments were run using
`m` = 8, 16, and 32. Also note that for PDQ, we want to tolerate distance
thresholds of up to 30, 40, or 50.

* 8-bit words: `m` = 32.
```
    d -> s:  0..31 -> 0. nnei  1 * 256. No precompute needed; also possible.
    d -> s: 32..63 -> 1. nnei 33 * 256. No precompute needed; also possible.
```

* 16-bit words: `m` = 16.
```
    d -> s:  0..15 -> 0. nnei   1 * 65536. No precompute needed; also possible.
    d -> s: 16..31 -> 1. nnei  17 * 65536. No precompute needed; also possible.
    d -> s: 32..47 -> 2. nnei 137 * 65536. No precompute needed; also possible.
    d -> s: 48..63 -> 3. nnei 697 * 65536. Nearest-neighbor table size too big.
```

* 32-bit words: `m` = 8.
```
    d -> s:  0..7  -> 0. nnei       1 * 4G. No precompute needed or possible
    d -> s:  8..15 -> 1. nnei      33 * 4G. No precompute needed or possible
    d -> s: 16..23 -> 2. nnei     529 * 4G. No precompute needed or possible
    d -> s: 24..31 -> 3. nnei    5489 * 4G. Slower and slower ...
    d -> s: 32..39 -> 4. nnei   41449 * 4G. ...
    d -> s: 40..47 -> 5. nnei  242825 * 4G. ...
    d -> s: 48..55 -> 6. nnei 1149017 * 4G. ...
    d -> s: 56..63 -> 7. nnei 4514873 * 4G. ...
```

Using 8-bit words:

* Benefit is that even for `d` = 63, `s` is just 1. This means it's easy to
  enumerate all slotwise nearest neighbors: table size 256 * 9.

* Fatal flaw is that there are only 256 possible values for each slot.
  This means the slotwise hashmaps are all big. The find-candidates step
  produces a huge number of candidates, all of which need to be pruned
  (and mostly rejected).

* Conclusion: 8-bit slots result in performance like linear search for
  any non-trivial dataset. Not usable for any non-trivial datasets, even
  with small `d`.

Using 32-bit words:

* Benefit is that there are 2^32 possible values for each slot. This means
  the slotwise hashmaps are all small. The find-candidates step produces
  a small number of candidates, for each slotwise nearest-neighbor.

* Flaw is that to get to hashwise `d`=31 (`s`=3), we need to examine over 5000
  slotwise nearest neighbors for each slot value; for `d`=63 (`s`=7), over 4
  million.

* Conclusion: 32-bit slots are stellar for tight hashwise distance
  thresholds, e.g. `d` <= 7. For the looser thresholds useful for PDQ,
  performance is unacceptable.

Using 16-bit words:

* Intermediate in both senses. Candidate-lists aren't too big; nearest
  neighbors aren't too many to loop over.

## Additional optimizations: slotwise-nearest-neighbor compute/tabulate

For 8-bit slots:

* It's possible to make a hardcoded 256x9 table of all `s`=0,1 slotwise
  nearest neighbors.

* It's also possible to compute the 1-bit flips dynamically on each
  needle lookup, although it's silly not to use the table.

For 16-bit slots:

* It's possible to make a hardcoded 65536x17 table of all `s`=0,1 slotwise
  nearest neighbors, although this adds to code size. For `s`=2,3 this gets
  out of hand.

* A second option is to keep a hashmap from all 65536 slot values to
  a hashset of their nearest neighbors.

  o When this is computed in the constructor, it's fast for `s`=0,1 but
    adds many seconds for `s`=2,3 and makes the test-lookups of toy-sized
    haystacks slower than necessary.

  o When these are lazily evaluated as needed, it's fast for `s`=0,1 but
    adds those same many seconds for `s`=2,3 amortized over the needle
    lookups.

  o Testing has shown that simply computing nearest neighbors dynamically
    via bitflips runs faster than the tabulated approach.

For 32-bit slots:

* Obviously, since there are 2^32 possible slot values, precomputing all
  nearest neighbors even for `s`=1 is prohibitive. And a lazy evaluation
  with hashmap storage would again (a) not get reuse in the small-haystack
  case, and (b) use up too much memory in the large-haystack case.

* For 32-bit slots we must dynamically compute slotwise nearest neighbors
  via bitflips.
