# Summary
vPDQ (Video PDQ) is a video-similarity-detection algorithm, which uses the PDQ image similarity algorithm on video frames to measure the similarity of videos.
Full details of PDQ are located in the [hashing.pdf](https://github.com/facebook/ThreatExchange/blob/main/hashing/hashing.pdf) document.
It allows for matching individual frames against known bad images, as well as which segments of a video are matching.
## Compared to TMK+PDQF
Compared to TMK+PDQF (TMK), which also relies on the PDQ image hashing algorithm:
TMK optimizes for identical videos (same length), vPDQ can match subsequences or clips within videos.
TMK has a fixed-length hash, which simplifies matching lookup, and can be near constant time with the help of FAISS. vPDQ produces a variable length hash, and requires a linear comparison of candidates. This requires either an O(n*F<sub>c</sub>*F<sub>q</sub>) lookup where n is the number of videos being compared, and F<sub>c</sub> is the average number of frames per compared video and F<sub>q</sub> is the number of frames in the source video, or an initial filtering pass to reduce the candidates, which can potentially discard matching videos.
Both TMK and vPDQ are backed by PDQ, and so inherit both PDQ’s strengths and weaknesses.

# Description of Algorithm
## Producing a Hash
The algorithm for producing the “hash” is simple: given a video, convert it into a sequence of frame images at some interval (for example, 1 frame/second). For each frame image, use the PDQ hashing algorithm on each.

We can annotate these hashes with their frame number, quality(0-100 which measures gradients/features,from least featureful to most featureful) and timestamp(sec). So for a 5 minute video at 1 frame/sec, we might have:
| Frame | Quality | PDQ Hash | Timestamp(sec) |
| ------------- | ------------- | ------------- | ------------- |
| 1  | 100 | face000...  | 0.000  |
| 2  | 99  | face000...  | 0.033  |
| 3  | 94  | face011...  | 0.067  |
| 4  | 97  | face111...  | 1.000  |
| ... | ...  |...  |...  |
| 29999 | 89  | 88784444... | 989.933 |
| 30000 | 92  | 88884444... | 989.967 |

For the matching algorithm, the frame numbers are not used, but they can still be useful for identifying matching segments when comparing videos.

### Pruning Frames
Often, many frames are repeated in a video, or frames are very close to each other in PDQ distance. It is possible to reduce the number of frames in a hash by omitting subsequent frames that are within a distance D<sub>prune</sub> of the last retained frame.

In the previous example, with D<sub>prune</sub> of 2 we might instead end up with:
| Frame | PDQ Hash | Distance from last retained frame| Result |
| ------------- | ------------- | ------------- |------------- |
| 1  | face000...  | N/A | Retain
| 2  | face000...  | 0 | Prune
| 3  | face011...  | 2 | Prune
| 4  | face111...  | 3 | Retain
| 5  | face111...  | 0 | Prune
| ... | ...  | ... | ... |

Afterwards, what is left is:
| Frame | PDQ Hash
| ------------- | ------------- |
| 1  | face000...  |
| 4  | face111...  |
| ... | ...  |

## Comparison (Matching) Algorithm
There are four inputs to the comparison algorithm, which determines if two videos are considered similar by vPDQ:
The query video’s frame PDQ hashes Q
The comparison video’s frame PDQ hashes C
The PDQ match distance D (example: 31)
The PDQ quality filter tolerance F (example: 50), if either hash is below this quality level then they will not be compared
The comparison match percentage threshold P<sub>c</sub> (example: 80%)
How much of the comparison video must be matched to consider a match
The query match percentage threshold P<sub>q</sub> (example: 0%)
Using a higher threshold will exclude videos with “extra” frames or content. 0% means don’t exclude matches based on padding in the uploaded video.
Using P<sub>c</sub> = 100% and P<sub>q</sub> = 100% will attempt to find only videos with the exact same frame content

Here is the algorithm, in pseudocode:
```
q_unique_frames  = set(Q)
c_unique_frames  = set(C)
q_unique_frames_matched_count = 0
c_unique_frames_matched_count = 0
q_unique_filtered_frames = filter(q_unique_frames, quality >= F)
c_unique_filtered_frames = filter(c_unique_frames, quality >= F)
for q_frame in q_unique_filtered_frames :
  for c_frame in c_unique_filtered_frames :
    if pdq_dist(q_frame, c_frame) <= D:
      q_unique_frames_matched_count++
      break

for c_frame in c_unique_filtered_frames :
  for q_frame in q_unique_filtered_frames :
    if pdq_dist(q_frame, c_frame) <= D:
      c_unique_frames_matched_count++
      break

q_pct_matched = q_unique_frames_matched_count * 100 / len(q_unique_filtered_frames)
c_pct_matched = c_unique_frames_matched_count * 100 / len(c_unique_filtered_frames)

is_match = c_pct_matched >= P_c and q_pct_matched >= P_q
```

As you can see, the frame number / ordering is not used at all in this comparison, and the frames are treated as an unordered “bag of hashes”.


### Pruning Candidates
When the number of potential candidates is high, the n*F<sub>c</sub>*F<sub>q</sub> algorithm might be too expensive to run. One potential solution for filtering is indexing frames from candidate videos into an index like FAISS, keyed to the video to compare. Our lookup algorithm then becomes:

```
candidate_video_ids = set()

for q_frame in Q:
  video_candidate_ids_with_frame = faiss_query(q_frame, D)
  for c_id in video_candidate_ids_with_frame:
    candidate_video_ids.add(c_id)

matching_candidates = []
for c_id in candidate_video_ids:
  C = lookup(c_id)
  is_match = vpdq_comparison(Q, C, D, P_c, P_q)
  if is_match:
    matching_candidates.add(C)

```

Beyond pruning frames from candidates, it may be desirable to further prune to just sampled or key frames in candidate videos to control index size, but this may result in videos being incorrectly pruned.

## CPP Implmentation
This implementation does not have Pruning Frames and Pruning Candidates.
### Getting started

#### Compile the code

```
$ cd cpp
$ mkdir build
$ cd build
$ cmake ..
$ make
```
Then you will have executable "vpdq-hash-video", "match-hashes-byline" and "match-hashes-brute". And two python scripts "vpdq_match.py" and "regtest.py" to run the executables. Please run executable with "-h" for more detailed reference information and usages.

#### Install FFmpeg

Before using VPDQ to create hashes, FFmpeg must be installed. (Easier to use if Accessible via the `$PATH` environment variable)

There are a variety of ways to install FFmpeg, such as the [official download links](https://ffmpeg.org/download.html), or using your package manager of choice (e.g. `sudo apt install ffmpeg` on Debian/Ubuntu, `brew install ffmpeg` on OS X, etc.).

Regardless of how FFmpeg is installed, you can check if your environment path is set correctly by running the `ffmpeg` command from the terminal, as in the following example (truncated for brevity):

```
$ ffmpeg
ffmpeg version 4.4.2 Copyright (c) 2000-2021 the FFmpeg developers
```

> **Note**: The actual version information displayed here may vary from one system to another; but if a message such as `ffmpeg: command not found` appears instead of the version information, FFmpeg is not properly installed.

#### Compute hashes of sample videos and compare to previous outputs
Hash the provided sample videos and compare the output hashes with sample hashes line by line.

```
cd cpp
python3 regtest.py -i ../ThreatExchange/tmk/sample-videos -d ../ThreatExchange/vpdq/output-hashes
Matching File pattern-sd-with-small-logo-bar.txt
100.000000 Percentage  matches

Matching File chair-20-sd-bar.txt
100.000000 Percentage  matches

Matching File doorknob-hd-no-bar.txt
100.000000 Percentage  matches

Matching File pattern-sd-with-large-logo-bar.txt
100.000000 Percentage  matches
...
Matching File chair-22-with-small-logo-bar.txt
100.000000 Percentage  matches
```

#### Look for matches between provided hashes and your own hashes
This demo shows how to use vpdq_match to compare one target hash with all the queried hashes in a folder.

#### Brute-force matching
```
cd cpp
python3 vpdq_match.py -f ../ThreatExchange/vpdq/sample-hashes -i ../ThreatExchange/vpdq/output-hashes/chair-19-sd-bar.txt
```
Sample Output:

```
Matching Target ../ThreatExchange/vpdq/cpp/sampletest/chair-19-sd-bar.txt with ../chair-22-with-large-logo-bar.txt
10.55 Percentage Query Video match
12.59 Percentage Target Video match

Matching Target ../ThreatExchange/vpdq/cpp/sampletest/chair-19-sd-bar.txt with ../chair-22-sd-sepia-bar.txt
67.76 Percentage Query Video match
80.85 Percentage Target Video match

Matching Target ../ThreatExchange/vpdq/cpp/sampletest/chair-19-sd-bar.txt with ../chair-19-sd-bar.txt
100.00 Percentage Query Video match
100.00 Percentage Target Video match
...

```

#### Faiss matching (Work in Progress)


## Contact

threatexchange@fb.com
