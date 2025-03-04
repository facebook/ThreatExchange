This file contains reference information.  Please see 
[README.md](https://github.com/facebook/ThreatExchange/blob/main/hashing/tmk/README.md)
for a higher-level walkthrough.

# Important executables

## tmk-hash-video

TMK requires all videos to be time-resampled to some common frame rate --
nominally 15 FPS. It also requires them to be image-resampled to common
dimensions -- 64x64 when PDQF is the framewise-feature algorithm. Both of these
are done using the `ffmpeg` executable -- which you need to separately install.

The `tmk-hash-video` takes the path to your `ffmpeg` executable and runs videos
through it as a preprocessor. Example:

```
$ ./tmk-hash-video -f /usr/local/bin/ffmpeg -i foo.mp4 -o foo.tmk
```

or

```
$ for v in ../sample-videos/*.mp4; do
  ./tmk-hash-video -f /usr/local/bin/ffmpeg -i $v -d .
done
```

```
$ ./tmk-hash-video -h
Usage: ./tmk-hash-video [options]
Required:
-f|--ffmpeg-path ...
-i|--input-video-file-name ...
-o|--output-feature-vectors-file-name ...
Optional:
-v|--verbose
-d|--output-directory ...: instead of specifying output-file name, just give a
  directory and the output file name will be auto-computed from the input video
  file name.
```

## tmk-compare-two-tmks

Sees if two `.tmk` files are the same, within roundoff error anyway. This is
**not** intended for video-matching between potential variations of a video --
see `tmk-query` for that. Rather, this program is intended for comparing hashes
of the **exact same video**, for regression or portability concerns.

Here we compare a hash to itself -- it should be equal:
```
$ tmk-compare-two-tmks misc-shelf-sd.tmk misc-shelf-sd.tmk
$ echo $?
0
```

Here we compare hashes of a standard-density video and a high-density version of the same video.
We'll see below that their pair scores are quite high (they are the same video at different
densities) but this `tmk-compare-two-tmks` program is checking to see if the hashes are
*identical* to within several decimal places. As expected, they're not.
```
$ tmk-compare-two-tmks misc-shelf-sd.tmk misc-shelf-hd.tmk
Tmk files do not match:
misc-shelf-sd.tmk
misc-shelf-hd.tmk
$ echo $?
1
```

```
$ tmk-compare-two-tmks -h
Usage: tmk-compare-two-tmks [options] {tmk file name 1} {tmk file name 2}
```

## tmk-clusterize

This is a naive technique for finding clusters of videos having pairwise cosine
similarity over a given threshold, e.g. 0.99 (where 1.0 is a perfect match).

* It only consults the time-average "level-1" feature.
* It uses no indexing so it requires O(N^2) cosine-similarity computations between each video-pairs' coarse features.  Nonetheless it runs on over 1000 feature-vector files in just a few seconds.
* It's a quick-peek way to look for similar videos within a collection.

```
$ tmk-clusterize -h
Usage: tmk-clusterize [options] [input file name]
Options:
--avg-only: Do not print cos/sin feature vectors.
-i:         Take feature-vector-file names from stdin, not argv.
-s:         Print a blank line between similarity clusters.
--c1 {x}: Level-1 threshold: default 0.700.
--c2 {y}: Level-2 threshold: default 0.700.
--level-1-only: Don't do level-2 thresholding (runs faster).
--min {n}:  Only print clusters of size n or more. Using 2
            suppresses output of singletons.
```

## tmk-query

This is the workhorse of the demo. It takes two text files, one containing
'needle' hash-file paths, and another containing 'haystack' hash-file paths. It
also takes level-1 and level-2 thresholds from the command line. It looks up
each 'needle' hash in the haystack and prints all matches (if any).

```
$ tmk-query -h
Usage: tmk-query [options] [needles file name] {haystack file name}
Needles file and haystack file should each contain .tmk file names,
one per line. Then the haystack .tmk files are loaded into memory.
Then each needle .tmk file is queried against the haystack, and all
matches within specified level-1/level-2 thresholds are printed.
Options:
-v|--verbose: Be more verbose.
--c1 {x}: Level-1 threshold: default -1.000.
--c2 {y}: Level-2 threshold: default 0.000.
```

## tmk-query-with-faiss

This is very similar to `tmk-query` but uses [faiss](https://github.com/facebookresearch/faiss) to run queries efficiently. faiss is a Facebook library for efficient similarity search and clustering of dense vectors.

```
$ tmk-query-with-faiss -h
Usage: tmk-query-with-faiss [options] [needles file name] {haystack file name}
Needles file and haystack file should each contain .tmk file names,
one per line. Then the haystack .tmk files are loaded into memory.
Then each needle .tmk file is queried against the haystack, and all
matches within specified level-1/level-2 thresholds are printed.
Options:
-v|--verbose: Be more verbose.
--c1 {x}: Level-1 threshold: default -1.000.
--c2 {y}: Level-2 threshold: default 0.000.
```

# Less important executables

## vstr2feat and feat2tmk

TMK has three stages, all done by the end-to-end hasher `tmk-hash-video`:

* Decode the video, time-resample to a common 15 FPS, and size-resample to 64x64 -- all using `popen` to `ffmpeg`
* Compute frame-features, i.e. 'frame hashes' one per frame
* Compute the TMK cosine/sine-weighted frame features.

If we need to do nitty-gritty cross-company debug, we can use these tools:

* The `ffmpeg` command inside of `tmk-hash-video.cpp` can be used to convert a video file to raw RGB frame rasters ('video stream' or 'vstr')
* `vstr2feat` can be used to take that and compute the frame-features, one feature (i.e. hash or vector) per frame. This goes into a `.feat` file.
* `feat2tmk` can be used to read that and compute TMK hashes per se, resulting in a `.tmk` file.

## featdump

Please disregard.  This is used for tapping out frame-features (before TMK
weighted averaging) which are an intermediate TMK processing step. These are
only produced by `vstr2feat`. Note: there is also a `tmk/tools/featdump.py`.

```
$ featdump -h
Usage: featdump [options] [input .feat file name]
If the input .feat file name is omitted, stdin is read.
Options:
--output-feature-vectors-file-name {x}
-v|--verbose
-r|--raw: Print only numbers and whitespace, no filenames.
```

## tmkdump

Displays TMK feature vectors from one or more `.tmk` files (see section below
on file formats), either all cosine/sine features, or just the time-average
'coarse' feature. There is also a `tmk/tools/tmkdump.py`.

```
$ tmkdump -h
Usage: tmkdump [options] [input file name]
If input file name is omitted, standard input is read.
Options:
--avg-only: Do not print cos/sin feature vectors.
-i:         Take feature-vector-file names from stdin, not argv.
-r|--raw:   Print only numbers and whitespace, no filenames.
```

## tmk-two-level-score

This computes level-1 pair score between **all pairs** of supplied hashes, and
for those pairs for which the level-1 score is over a specified threshold,
computes the level-2 pair score as well. This is useful for plotting the
"shape" of the probability space of pairwise hashes: what they look like for
known-unrelated videos, and known-related videos.

```
$ tmk-two-level-score -h
Usage: tmk-two-level-score [options] [input file name]
Options:
-i:       Take feature-vector-file names from stdin, not argv.
--c1 {x}: Level-1 threshold: default 0.700.
--c2 {y}: Level-2 threshold: default 0.700.
--include-self: Match each hash against itself as well as others.
```

## tmk-show-pair-offsets

Please disregard. Given two video hashes, tries to find alignment between their matching subsequences. Not used at present.

```
$ tmk-show-pair-offsets -h
Usage: tmk-show-pair-offsets [options] {tmk file name 1} {tmk file name 2}
Options:
-v|--verbose Print details of K-delta results.
```

# File formats

Goals:

* Binary I/O due to the large numbers of floating-point data. I really really really prefer text files whenever appropriate but here is a time they are not appropriate.
* But raw binaries convey zero structure information. A person could read a frame-features file as if it were a frame-rasters file or feature-vectors file and disaster would ensue. So I use a 32-byte header for all files, with magic numbers for each, with read/write methods that error-check on these formats. These help our industry partners (as well as ourselves) use data files in robust and trustable ways.

The formats are:

* `.vstr`: decoded video stream: from `vid2vstr` to `vstr2feat`
* `.feat`: time-resampled frame descriptors: from `vstr2feat` to `feat2tmk`
* `.tmk`: TMK cosine/sine feature vectors, AKA the TMK hash: output from `feat2tmk`.
* `tmk-hash-video` is end-to-end from `.mp4` to `.tmk` without tapping out intermediaries.

The exact file formats are in `tmktypes.h` but as of 2018-05-01 they look like:

```
# The header includes the dimensions of the data
$ hex ~/wideband/tmk/vstr/misc-shelf-sd.vstr | head
00000000: 54 4d 4b 31  56 53 54 52  90 01 00 00  e0 00 00 00 |TMK1VSTR........| HEADER LINE 1
00000010: 0f 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00 |................| HEADER LINE 2
00000020: 3d 47 61 3d  47 61 3d 47  61 3d 47 61  3d 47 61 3d |=Ga=Ga=Ga=Ga=Ga=| START OF RGB FRAME-RASTER DATA
00000030: 47 61 3d 47  61 3d 47 61  3d 47 61 3d  47 61 3d 47 |Ga=Ga=Ga=Ga=Ga=G|
00000040: 61 3d 47 61  3d 47 61 3d  47 61 3d 47  61 3d 47 61 |a=Ga=Ga=Ga=Ga=Ga|
00000050: 3e 48 62 3e  48 62 3d 47  61 3d 47 61  3d 47 61 3b |>Hb>Hb=Ga=Ga=Ga;|
00000060: 45 5f 3a 44  5e 3a 44 5e  38 42 5c 38  42 5c 37 41 |E_:D^:D^8B\8B\7A|
00000070: 5b 36 40 5a  36 40 5a 34  3e 58 34 3e  58 34 3e 58 |[6@Z6@Z4>X4>X4>X|
00000080: 33 3d 57 33  3d 57 33 3d  57 33 3d 57  33 3d 57 33 |3=W3=W3=W3=W3=W3|
00000090: 3d 57 32 3c  56 32 3c 56  30 3a 54 30  3a 54 2f 39 |=W2<V2<V0:T0:T/9|

# The header includes the dimensions of the data
$ hex ~/wideband/tmk/feat/pdqf/misc-shelf-sd.feat | head
00000000: 54 4d 4b 31  46 45 41 54  50 44 51 46  00 01 00 00 |TMK1FEATPDQF....| HEADER LINE 1
00000010: 0f 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00 |................| HEADER LINE 2
00000020: 37 2b 8c c3  7a 84 3c 44  39 ea ef c3  dd c0 09 44 |7+..z.<D9......D| START OF FRAME FEATURES
00000030: de a2 63 41  e8 4e 31 43  62 d5 61 c3  82 ff 5c 43 |..cA.N1Cb.a...\C|
00000040: f9 f7 5e c3  5a 7a 23 43  ba 87 69 42  fc df 57 c1 |..^.Zz#C..iB..W.|
00000050: 5b e4 8e 42  89 7c 1b c3  87 22 53 42  8c ec 82 c0 |[..B.|..."SB....|
00000060: 24 71 5f 41  0c d9 0b 42  f7 10 b8 c2  64 43 9a 43 |$q_A...B....dC.C|
00000070: 16 85 ed c3  aa f9 b9 42  7c 5e ba c3  bc f1 2b 43 |.......B|^....+C|
00000080: 14 fc 0a 43  5c a5 10 c2  b4 e2 78 43  98 e2 dc c3 |...C\.....xC....|
00000090: c7 89 2b 43  b6 08 13 c2  bc 6d cc 42  a8 52 d0 42 |..+C.....m.B.R.B|

# The header includes the dimensions of the data
$ hex ~/wideband/tmk/fvec/pdqf/misc-shelf-sd.tmk | head
00000000: 54 4d 4b 31  46 56 45 43  50 44 51 46  04 00 00 00 |TMK1FVECPDQF....| HEADER LINE 1
00000010: 04 00 00 00  20 00 00 00  00 01 00 00  00 00 00 00 |.... ...........| HEADER LINE 2
00000020: ab 0a 00 00  27 11 00 00  27 26 00 00  3d 39 00 00 |....'...'&..=9..| START OF FEATURE VECTORS
00000030: 06 3d 88 3e  91 25 bf 3e  66 a6 ba 3e  ee 64 b3 3e |.=.>.%.>f..>.d.>|
00000040: af b7 a9 3e  01 0e 9e 3e  9d e7 90 3e  76 cb 82 3e |...>...>...>v..>|
00000050: 8f 7d 68 3e  4c 7a 4b 3e  79 64 2f 3e  0b eb 14 3e |.}h>LzK>yd/>...>|
00000060: 96 20 f9 3d  10 53 cd 3d  1e c4 a6 3d  45 81 85 3d |. .=.S.=...=E..=|
00000070: c3 b9 52 3d  8a fa 23 3d  1d ae fb 3c  5f 83 be 3c |..R=..#=...<_..<|
00000080: 7a 46 8e 3c  90 b0 51 3c  12 82 18 3c  28 fd da 3b |zF.<..Q<...<(..;|
00000090: 2e 3c 9b 3b  36 57 59 3b  91 47 16 3b  60 4f cd 3a |.<.;6WY;.G.;`O.:|
```
