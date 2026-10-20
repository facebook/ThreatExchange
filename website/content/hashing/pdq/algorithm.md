---
prev:
  text: Overview
# next:
#   text: Implementations
#   # link: /hashing/pdq/implementations
---

# PDQ Algorithm

PDQ is a perceptual image-hashing algorithm. Unlike a cryptographic hash, which changes dramatically when input bytes change, a perceptual hash is designed to produce similar values for images that look similar to people.

PDQ uses a Discrete Cosine Transform (DCT), a spectral-analysis technique commonly used in image processing. It produces:

- A 256-bit hash representing visual characteristics of the image.
- A quality score indicating how suitable the image is for matching. Featureless or low-quality images can be filtered out.

Two PDQ hashes can be compared using Hamming distance: the number of differing bits. A smaller distance indicates greater similarity, but thresholds should be validated against the content and false-positive/false-negative tradeoffs of each application.

As a starting point, the project recommends:

- Hamming distance `<= 31` for considering hashes similar.
- Discarding hashes with quality `<= 49`.

These are starting points, not universal guarantees. PDQ is intended for similarity detection, not cryptographic integrity, authentication, or proof that two files are identical.

PDQ implementations are available in C++, PHP, Python, Java, and WebAssembly. See the [implementation guide](./implementations) and the [PDQ reference implementations](https://github.com/facebook/ThreatExchange/tree/main/pdq).

For a detailed description of the algorithm, see the [PDQ hashing paper](https://github.com/facebook/ThreatExchange/blob/main/hashing/hashing.pdf).
