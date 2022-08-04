# Summary
The description of vPDQ algorithm hashing and brute-force matching can be found in [vpdq/README.md](../../../../vpdq/README.md). This README describes the [FAISS](https://github.com/facebookresearch/faiss) matching process which is integrated with the vPDQ index in python-threatexchange.

#### Faiss matching
vPDQ features are a list of PDQ hashes embedded with Frame, Quality, and Timestamp(sec). When added to FAISS index, only PDQ hashes are indexed. Thus, extra information is stored in the wrapper index class to reformat the vPDQ feature when returning the results for searching. When we want to match a video (a list of vPDQ features) against the index, we also only input the PDQ hashes to search.

A query on the index is comprised of a sequence of individual PDQ hashes. Each of which will have a corresponding set of matches returned that were within threshold hamming distance of that query (or none in the case that specific hashes did not match anything in the index). These matches will be (idx, distance).
The inner sequences may be empty in the case of no hashes within the index.
The same VPDQ feature may also appear in more than one inner sequence if it matches multiple query hashes.
For example the hash "000000000000000000000000000000000000000000000000000000000000ffff" would match both
"00000000000000000000000000000000000000000000000000000000fffffff" and
"0000000000000000000000000000000000000000000000000000000000000000" for a threshold of 16. Thus it would appear in
the entry for both the hashes if they were both in the queries list.

e.g.
query_str =>  (idx, distance)
result = {
    "000000000000000000000000000000000000000000000000000000000000ffff": [
        (12345678901, 16.0)
    ]
}

To calculate the percentage of query matching and index matching (i.e. what percentage of frames in the search video query appear in the index and vice versa), two unique sets are used in the wrapper class to count the number of matches.

The query video’s frame PDQ hashes Q
Two unique comparison videos' frame PDQ hashes C1,C2
The PDQ match distance D (example: 31)
The PDQ quality filter tolerance F (example: 50), if either hash is below this quality level then they will not be compared
Here is the algorithm, in pseudocode:

Build Index
```
index = FAISS()
q_unique_frames = set(Q)
c1_unique_frames = set(C1)
c2_unique_frames = set(C2)
q_unique_filtered_frames = filter(q_unique_frames, quality >= F)
c1_unique_filtered_frames = filter(c1_unique_frames, quality >= F)
c2_unique_filtered_frames = filter(c2_unique_frames, quality >= F)
idx_to_vpdq_and_video_id = list()
video_id_to_vpdq = list()
video_id_to_vpdq.insert(1, c1_unique_frames)
video_id_to_vpdq.insert(2, c2_unique_frames)
idx_to_vpdq_and_video_id.append((c1_unique_frames, 1))
idx_to_vpdq_and_video_id.append((c2_unique_frames, 2))
index.add(c1_unique_filtered_frames)
index.add(c2_unique_filtered_frames)
```

Search and Process Result
```
results = FAISS_index.search(q_unique_filtered_frames, D)
query_matched: Dict() (int, set())
index_matched: Dict() (int, set())
for match_result in results :
    for match_hash in results[match_result] :
        # match_hash =>  (idx, distance)
        vpdq_match, video_id = idx_to_vpdq_and_video_id[match_hash[0]]
        query_matched[video_id].add(match_hash)
        query_matched[video_id].add(vpdq_match)

for query_video_id in  query_matched.keys():
    query_matched_percent = len(query_matched[query_video_id]) * 100 / len(q_unique_filtered_frames)
    index_matched_percent = (len(index_matched[query_video_id])* 100 / len(video_id_to_vpdq[query_video_id])
```

However, this only works for two unique comparison videos, because FAISS will replace the same existing pdqHash. For example, if c1 and c2 share a same frame hash SF. When adding to the index in order c1-c2, c2's SF will replace c1's SF. Then, the search for SF will only return the second SF's idx(c2's hash) and we will lose the match result in c1. Thus, a preprocess is required before adding frame hashes into the idx_to_vpdq_and_video_id separately with its video_id:
```
unique_vpdq_to_idx = Dict() (vpdq, int)
unique_frames = set()
for c1_frame in c1_unique_filtered_frames:
        idx = unique_vpdq_to_idx.get(c1_frame)
        if idx is None:
            idx = len(unique_vpdq_to_idx)
            unique_vpdq_to_idx[c1_frame] = idx
            idx_to_vpdq_and_video_id.append((c1_frame, 1))
            unique_frames.append(c1_frame)
        idx_to_vpdq_and_video_id[idx][1].append(1) 
        # Duplicate hashes won't be added to the index but instead add its video_id to the existing hash's video_id list
index.add(unique_frames)
```


#### Benchmark
The benchmark tests building index and searching between brute-force, raw FAISS and vPDQ index (with FAISS). The result is presented at [python-threatexchange/benchmarks/README.MD](../../../benchmarks/README.MD)