# pytx-vPDQ
Benchmark vPDQ implementation & PDQ Faiss matchers in the threatexchange library.


# Observed Performance
- Model: MacBook Air
- Memory: 16 GB
- Operating System: macOS 15.2
- Chip: Apple M2
- Core Configuration: 8 cores total


Results (vPDQ):
-------
```
% python3 benchmark_vpdq_index.py brute_force -f 500 -v 20  -q 1000
build: 0.0000s
query: 684.5324s
  Per query: 684.5324ms


% python3 benchmark_vpdq_index.py flat -f 500 -v 20 -q 1000
build: 0.0048s
query: 0.0051s
  Per query: 0.0051ms


% python3 benchmark_vpdq_index.py signal_type -f 500 -v 2000 -q 10000
Generating data...
Generating data: 1.2398s
build: 3.2970s
query: 2.8439s
  Per query: 0.2844ms


% python3 benchmark_vpdq_index.py flat -f 500 -v 2000 -q 10000
Generating data...
Generating data: 1.2237s
build: 0.4786s
query: 2.5248s
  Per query: 0.2525ms


% python3 benchmark_vpdq_index.py flat -f 500 -v 2000 -q 100000
Generating data...
Generating data: 1.2195s
build: 0.4800s
Generating queries...
Generating queries: 0.1017s
query: 26.0294s
  Per query: 0.2603ms
```

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
	PDQFlatHashIndex - Precent of targets found:  100.0
	PDQMultiHashIndex - Precent of targets found:  100.0
```
