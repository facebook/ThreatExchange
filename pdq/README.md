# PDQ reference implementation
<img src="./pdq_blue_transparent.png" width="256">

## Description

This is a collection of reference implementation for the PDQ hashing algorithm.

Please see [../hashing.pdf](https://github.com/facebook/ThreatExchange/blob/main/hashing/hashing.pdf)
within this repository for an explanation of the algorithm.

See also the [Meta Newsroom Post](https://newsroom.fb.com/news/2019/08/open-source-photo-video-matching) for context.

As of November 2018 there are C++, PHP, and Java implementations.  Details are in the `*/README.md` files.

## Other Bindings and Implementations
* Python: [faustomorales/pdqhash-python](https://github.com/faustomorales/pdqhash-python)
* Rust: [darwinium-com/pdqhash](https://github.com/darwinium-com/pdqhash) - a great visualization of the algorithm also lives here.

## Writing Your Own Hashing & Matching Implementations
You can find a reference end-to-end hashing and matching solution in [facebook/ThreatExchange/python-threatexchange](https://github.com/facebook/ThreatExchange/tree/main/python-threatexchange). This tends to be the fastest way to install and play with the algorithm. You can see the implementation of the [PDQ SignalType for references for potential thresholds](https://github.com/facebook/ThreatExchange/blob/main/python-threatexchange/threatexchange/signal_type/pdq/signal.py)

### Hashing
PDQ is heavily dependent on platform specific libraries to convert images into byte arrays. Even with the same exact images, you may get different PDQ hash values with different languages or underlying libraries. 

We have generally considered implementations to be "correct" if, using images from the pdq/data directory, both of these are true:
1. Generating byte arrays from the C++ reference implementation and then piping them into the new implementation produces the exact same hash as the C++ reference implementation
2. Hashes produced by an implementation where quality score >= 80 are within distance <= 10 of the C++ reference implementation

These guidelines were determined by experimentation and not by any rigorous methodology, and so may be adjusted in the future.

### Matching
You can see the implementation of the [PDQ SignalType for references for scaled matching](https://github.com/facebook/ThreatExchange/blob/main/python-threatexchange/threatexchange/signal_type/pdq/signal.py). The faiss matching implementation has been proven up to 4000 images/sec. [HMA](https://github.com/facebook/ThreatExchange/wiki) is built on a similar implementation.

Before evaluating the results on your own to choose the thresholds that work for you, we recommend starting with:

* **Distance Threshold to consider two hashes to be similar/matching**: <=31
* **Quality Threshold where we recommend discarding hashes**: <=49

## Note on Dihedral PDQ Hashes

The PDQ hashing algorithm is easily capable of producing eight "dihedral" hashes (one for each 90 degree rotation and one for each flip across a horizontal, vertical or diagonal axis). However, PDQ does not guarantee exact rotational invariance. Small variations can occur in the hash values for each rotation due to how PDQ processes the image’s grid alignment in its DCT (Discrete Cosine Transform) phase.

For example, two rotated versions of an image can have a slightly different set of eight dihedral hashes. Selecting a "minimal" hash from these transformations (e.g., lexicographically) may yield inconsistent results because of these minor bit differences. For each image, if we select the minimal hash, there’s no guarantee that the same hash will be selected across different rotations. These inconsistencies arise when small bit variations lead to a different hash being identified as "minimal" for each rotation. For a clearer example, check this issue: ([https://github.com/facebook/ThreatExchange/issues/1676#issuecomment-2466331532](https://github.com/facebook/ThreatExchange/issues/1676#issuecomment-2466331532)).

## Contact

threatexchange@meta.com
