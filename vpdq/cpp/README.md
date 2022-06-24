# Documentation

Please see [../README.md](https://github.com/facebook/ThreatExchange/blob/main/vpdq/README.md) and [../../README.md](https://github.com/facebook/ThreatExchange/blob/main/README.md) for context, and [../hashing.pdf](https://github.com/facebook/ThreatExchange/blob/main/hashing/hashing.pdf) for thorough documentation.

# Dependencies

* C++ 14 or higher
* `ffmpeg` command-line executable somewhere on your system
* FAISS (<https://github.com/facebookresearch/faiss>) is optional. Its integration into this repository is a work in progress (you can build without it).

## MacOS on Apple M1

* Currently the builtin Apple clang g++ does not work for building this implementation.
* Installing gcc and updating the `CMake`s CXX to use that version of g++ instead is recommend.
