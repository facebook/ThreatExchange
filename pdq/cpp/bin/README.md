# PDQ reference implementation

## Description

This is the reference implementation for the PDQ hashing algorithm, FB-ified (buck build, etc.).

Please see https://github.com/facebookexternal/ThreatExchange-PDQ/

### Ops-tool/demo mains

* `pdq-photo-hasher.cpp` -- Runs the PDQ hashing algorithm and produces hashes+metadata+timings. Use `mlr` (https://github.com/johnkerl/miller) to slice & dice the output if you like.
* `hashtool256.cpp` -- Various operations on 256-bit hashes for operational use. See `reg_test/run` for sample invocations and `reg_test/expected/out` for sample output.
* `clusterize256.cpp` -- Given a list of hashes+metadata, clusterizes it against itself.
* `mih-query.cpp` -- Given two lists of hashes+metadata ('needles' and 'haystack'), looks up each of the former in the latter.

### Visualizers

These are all Ruby scripts.

* ` htmlify-photos.rb` -- Reads the output of `pdq-photo-hasher` and writes simple HTML for visualizing.
* ` htmlify-photos-plain.rb` -- Same but with no text, only images. For the "Definition and evaluation of quality metric" section of the PDQ hashing document, I did `pdq-photo-hasher ...` to a file, then piped that to `mlr sort -n quality`, then piped that to `htmlify-photos-plain.rb` and screenshotted that.
* ` htmlify-pairs.rb` -- Same but pairs up images from two files. Used for the part of the PDQ hashing document which pairs up video frames with/without watermarks.
* ` htmlify-clusters.rb` -- Reads the output of `clusterize256` and writes simple HTML for visualizing.
* ` htmlify-clusters-plain.rb` -- Same but with no text, only images. See for example the "Clustering results" section of the PDQ hashing document.

## Examples

* Test run of the hasher:
```
$ ./pdq-photo-hasher reg_test/input/dih/bridge-*jpg
f8f8f0cce0f4e84d0e370a22028f67f0b36e2ed596623e1d33e6339c4e9c9b22,reg_test/input/dih/bridge-1-original.jpg
b0a10efd71cc3f429413d48d0ffffe12e34e0e17ada952a9d29684210aa9e5af,reg_test/input/dih/bridge-2-rotate-90.jpg
adad5a64b5a142e55362a09057dacd5ae63b847fc23794b766b319361fc93188,reg_test/input/dih/bridge-3-rotate-180.jpg
a5f4a457a48995e8c9065c275aaa5498b61ba4bdf8fcf80387c32f8b0bfc4f05,reg_test/input/dih/bridge-4-rotate-270.jpg
f8f80f31e0f417b00e37f5cd028f980fb36ed02a9662c1e233e6cc634e9c64dd,reg_test/input/dih/bridge-5-flipx.jpg
8dad2599b1a1bd1853625f6553da32a1e63b7280c2374b4866b366c91bc9ce77,reg_test/input/dih/bridge-6-flipy.jpg
f0a1f102f1dcc0bd9c5309720fff018de34ef1e8ada9a956d2967ade0ea91a50,reg_test/input/dih/bridge-7-flip-plus-1.jpg
a5f05ba8a4896a17c106a3da5aaaab07b61b5b42f8fc07fc83c3d0740bfcb0fa,reg_test/input/dih/bridge-8-flip-minus-1.jpg
```

* Get some image files, some matching the above and some not.
* `pdq-photo-hasher --details /path/to/your/*.jpg > haystack.hsh`.
* `clusterize256 haystack.hsh > haystack.clu` and verify that similars are clustered together.
* Run `htmlify-clusters.rb < haystack.clu > haystack.html` and open that file in your browser to take a look at the images.
* Get some more image files.
* `pdq-photo-hasher --details /path/to/more/*.jpg > needles.hsh`.
* `mih-query needles.hsh haystack.hsh` and verify that matches are found as desired.
