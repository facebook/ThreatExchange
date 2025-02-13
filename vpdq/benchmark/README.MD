# pytx-vpdq
Benchmark vPDQ CPP implementation and python-binding library


# Observed Performance
MacBook Pro (16-inch, 2021), Apple M1 Pro, 32 GB Ram

Results:
-------
```
% python3 benchmark.py      
Python hashing time: 34.1643s
  Total hash: 7069  Per hash: 4.8330ms
CPP hashing time: 34.3673s
  Total hash: 7069  Per hash: 4.8617ms

% python3 benchmark.py -r 1 
Python hashing time: 6.9934s
  Total hash: 241  Per hash: 29.0182ms
CPP hashing time: 7.3139s
  Total hash: 241  Per hash: 30.3483ms

% python3 benchmark.py -s 540
Python hashing time: 20.5453s
  Total hash: 7069  Per hash: 2.9064ms
CPP hashing time: 20.9247s
  Total hash: 7069  Per hash: 2.9601ms
Calculate deviations in downsampled hashes, since hash resolution is non-native
Original resolution Python hashing time: 33.9340s
  Number of mismatches: 0, 0.00 percent in total.
  Average 7.99 hamming distance away.

% python3 benchmark.py -s 360
Python hashing time: 9.8740s
  Total hash: 7069  Per hash: 1.3968ms
CPP hashing time: 10.2460s
  Total hash: 7069  Per hash: 1.4494ms
Calculate deviations in downsampled hashes, since hash resolution is non-native
Original resolution Python hashing time: 34.5316s
  Number of mismatches: 0, 0.00 percent in total.
  Average 8.57 hamming distance away.

% python3 benchmark.py -s 180
Python hashing time: 4.8490s
  Total hash: 7069  Per hash: 0.6860ms
CPP hashing time: 5.4182s
  Total hash: 7069  Per hash: 0.7665ms
Calculate deviations in downsampled hashes, since hash resolution is non-native
Original resolution Python hashing time: 34.8951s
  Number of mismatches: 121, 0.02 percent in total.
  Average 17.63 hamming distance away.

python3 benchmark.py -s 64
Python hashing time: 3.1143s
  Total hash: 7069  Per hash: 0.4406ms
CPP hashing time: 3.5193s
  Total hash: 7069  Per hash: 0.4979ms
Calculate deviations in downsampled hashes, since hash resolution is non-native
Original resolution Python hashing time: 35.2615s
  Number of mismatches: 20, 0.00 percent in total.
  Average 9.39 hamming distance away.

% python3 benchmark.py -s 60 
Python hashing time: 3.0915s
  Total hash: 7069  Per hash: 0.4373ms
CPP hashing time: 3.3920s
  Total hash: 7069  Per hash: 0.4798ms
Calculate deviations in downsampled hashes, since hash resolution is non-native
Original resolution Python hashing time: 34.4134s
  Number of mismatches: 153, 0.02 percent in total.
  Average 17.71 hamming distance away.
```

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
