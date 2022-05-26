# Dependencies

* C++ 14 or higher
* `ffmpeg` command-line executable somewhere on your system
* FAISS (<https://github.com/facebookresearch/faiss>) is optional. Its integration into this repository is a work in progress (you can build without it).

## MacOS on Apple M1

* Currently the builtin Apple clang g++ does not work for building this implementation.
  * Installing gcc and updating the `Makefile`s CXX to use that version of g++ instead is recommend.
