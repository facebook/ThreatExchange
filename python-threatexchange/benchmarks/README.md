# pytx-PDQ
Benchmark PDQ Faiss matchers in the threatexchange library.


# Observed Performance
- Model: MacBook Air
- Memory: 16 GB
- Operating System: macOS 15.2
- Chip: Apple M2
- Core Configuration: 8 cores total


Results (PDQ Faiss):
-------
```
% python3 benchmarks/benchmark_pdq_faiss_matchers.py --dataset-size 10000 --num-queries 1000 --thresholds 31
Benchmark: PDQ Faiss Matcher Comparison

Options:
	 faiss_threads :  1
	 dataset_size :  10000
	 num_queries :  1000
	 thresholds :  [31]
	 seed :  None

using random seed of  1739236966565067000
use --seed  1739236966565067000  to rerun with same random values

Building Stats:
	PDQFlatHashIndex: time to build (s):  0.015399932861328125
	PDQFlatHashIndex: approximate size: 390KB
	PDQMultiHashIndex: time to build (s):  0.030457258224487305
	PDQMultiHashIndex: approximate size: 1,207KB

Benchmarks for threshold:  31
	PDQFlatHashIndex - Total Time to search  (s):  0.012083053588867188
	PDQMultiHashIndex - Total Time to search  (s):  0.01529383659362793
	PDQFlatHashIndex - Percent of targets found:  100.0
	PDQMultiHashIndex - Percent of targets found:  100.0
```
