# PDQ reference implementation: Java

## Description

This is the Java reference implementation for the PDQ hashing algorithm.

Please see `../../LICENSE.txt`, as well as `../../hashing.pdf`, within this repository.

## Building

There's a very simple `Makefile` which you can adapt; there is also a Maven config.  There is nothing special: just Java with no external dependenciees. It was developed and tested with Java 8, but it uses no Java-8 features. Alternatively, `mvn install`, but note that this will not run the `./reg_test/run` regression script, which the `Makefile` will run.

We've built and run this code on Linux (CentOS) and MacOSX.


This is Java code which we've tried to make non-clever. If people want another implementation, such as Python, let's discuss and work together. Ports should be done once, without several of us doing duplicated work porting to another language. 

As of 2017-11-08 there is also a **pure-PHP** implementation for the hasher, but not yet for the hash-lookup (MIH) logic; the **C++** and **Java** implementations are complete.

##

Building using bazel:
https://bazel.build/
bazel build //...
bazel run //src/main/java/tools:ToolName

## Portability concerns

The regression script invoked by the Makefile invokes a clusterizer which depends on iteration order through hash maps. This means that if you run it on the same machine/platform you should get the same results; this is good for checking if you recently broke something.

## Source-code tour

### Build/verify files

* `Makefile` -- as above.
* `./reg_test/run` -- a shell script which is invoked by the makefile and which compares various outputs against expecteds.

OR

* `mvn clean test install` -- Compiles the code in src/main/java folder, tests it and creates the jar under target/ folder.
* `cp target/pdq-0.0.1-SNAPSHOT.jar pdq.jar` -- Copies the newly created jar and overwrites the jar created via Makefile.
* `./reg_test/run` -- a shell script which is invoked by the makefile and which compares various outputs against expecteds.

### Library files

* `pdqhashing/types/Hash256.java` -- the `Hash256` datatype.
* `pdqhashing/hasher/PDQHasher.java` -- The PDQ hashing algorithm per se, operating entirely on matrices of RGB byte-triples (or greyscale bytes). Everything here is completely independent of file formats such as JPEG, PNG, MP4 frames, etc. etc.
* `pdqhashing/indexer/MIH256.java` -- Mutually-indexed hashing as in Norouzi et al. 2014. Feel free to substitute your own indexing for bit-vectors if you have and prefer it. What's essential for cross-industry hash-sharing is that the same photos produce the same hashes. What mechanisms we use within our own companies to index those for search is a matter of local taste. Nonetheless, we offer MIH as an option.
* `pdqhashing/utils/HashReaderUtil.java` -- utility routines for loading hashes, or hashes+metadata, from files.

### Ops-tool/demo mains

* `bin/pdq-photo-hasher-tool` is a shell script which fronts `pdqhashing/tools/PDQPhotoHasherTool.java` -- A `main` method for computing PDQ hashes of image files.
* `bin/hash256tool` is a shell script which fronts `pdqhashing/tools/Hash256Tool.java` -- A `main` method for doing various arithmetic on hashes.
* `bin/mih-query-tool` is a shell script which fronts `pdqhashing/tools/MIHQueryTool.java` -- A `main` method which demonstrates how to look up a supplied list of 'needle' hashes within another list of 'haystack' hashes.
* `bin/clusterize256-tool` is a shell script which fronts `pdqhashing/tools/Clusterize256Tool.java` -- A `main` method for a similarity clusterizer.
* `bin/clusterize256x-tool` is a shell script which fronts `pdqhashing/tools/Clusterize256xTool.java` -- Similar to the previous, but operates better on large amounts of data, while requiring a separate post-processing step.

### Visualizers

See the `../cpp` directory.

### Clusterizer visualization

```
$ cd ../cpp
$ find /path/to/image/files -name '*g' | pdq-photo-hasher -i --details | tee cpp-output.hsh
$ ./clusterize256 cpp-output.hsh > cpp-output.clu
$ ./htmlify-clusters-plain.rb cpp-output.clu > cpp-output.html

$ cd ../java
$ find /path/to/image/files -name '*g' | bin/pdq-photo-hasher-tool -i --details | tee java-output.hsh
$ ./bin/clusterize256-tool java-output.hsh > java-output.clu
$ ../cpp/htmlify-clusters-plain.rb java-output.clu > java-output.html
```

Then inspect both HTML files.

### Evaluation

See `../cpp/evaluation-notes.txt`.

## What you can do to get started

* `cd` into the `java` subdirectory.
* Run `make` and ensure that the regression tests pass. Please contact us ASAP with any issues. If you see a few two-bit differences on image files, this is a known lack-of-portability issue with `CImg` (which is in turn only for evaluation -- for production, please use your own decoders). Run `make itso` to accept the differences locally.
* The regression test runs the bridge examples above, so if that passes, we've got baseline sanity established for computing hashes. Example:
```
$ ./bin/pdq-photo-hasher-tool reg_test/input/dih/bridge-*jpg
f8f8f0cce0f4e84d0e370a22028f67f0b36e2ed596623e1d33e6339c4e9c9b22,100,reg_test/input/dih/bridge-1-original.jpg
b0a10efd71cc3f429413d48d0ffffe12e34e0e17ada952a9d29684210aa9e5af,100,reg_test/input/dih/bridge-2-rotate-90.jpg
adad5a64b5a142e55362a09057dacd5ae63b847fc23794b766b319361fc93188,100,reg_test/input/dih/bridge-3-rotate-180.jpg
a5f4a457a48995e8c9065c275aaa5498b61ba4bdf8fcf80387c32f8b0bfc4f05,100,reg_test/input/dih/bridge-4-rotate-270.jpg
f8f80f31e0f417b00e37f5cd028f980fb36ed02a9662c1e233e6cc634e9c64dd,100,reg_test/input/dih/bridge-5-flipx.jpg
8dad2599b1a1bd1853625f6553da32a1e63b7280c2374b4866b366c91bc9ce77,100,reg_test/input/dih/bridge-6-flipy.jpg
f0a1f102f1dcc0bd9c5309720fff018de34ef1e8ada9a956d2967ade0ea91a50,100,reg_test/input/dih/bridge-7-flip-plus-1.jpg
a5f05ba8a4896a17c106a3da5aaaab07b61b5b42f8fc07fc83c3d0740bfcb0fa,100,reg_test/input/dih/bridge-8-flip-minus-1.jpg
```

* Get some image files, some matching the above and some not.
* `bin/pdq-photo-hasher-tool --details /path/to/your/*.jpg > haystack.hsh`.
* `bin/clusterize256-tool haystack.hsh > haystack.clu` and verify that similars are clustered together.
* Run `../cpp/htmlify-clusters.rb < haystack.clu > haystack.html` and open that file in your browser to take a look at the images.
* Get some more image files.
* `bin/pdq-photo-hasher-tool --details /path/to/more/*.jpg > needles.hsh`.
* `bin/mih-query-tool needles.hsh haystack.hsh` and verify that matches are found as desired.

## Contact

threatexchange@meta.com

2018-01-21
