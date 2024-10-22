# Documentation

Please see [../README.md](https://github.com/facebook/ThreatExchange/blob/main/pdq/README.md) and [../../README.md](https://github.com/facebook/ThreatExchange/blob/main/README.md) for context, and [../hashing.pdf](https://github.com/facebook/ThreatExchange/blob/main/hashing/hashing.pdf) for thorough documentation.

# Dependencies

* C++ 11 or higher
* `CImg.h` is included for reference, though note it is not under the same license as the rest of the repository. It is expected that your company will already have image-processing logic. Dependencies of this code on `CImg.h` are confined solely to `io/pdqio.h` and `io/pdqio.cpp` which you can customize for your site.
* ImageMagick or other JPEG/PNG libraries: for example, `brew install imagemagick` on MacOSX

## MacOS on Apple M1

* Currently the builtin Apple clang g++ does not work for building this implementation.
  * Installing gcc and updating the `Makefile`s CXX to use that version of g++ instead is recommend.

# Contact

threatexchange@meta.com
