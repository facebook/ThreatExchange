# pytx-vpdq
Benchmark vPDQ implementation in threatexchange library


# Observed Performance
MacBook Pro (16-inch, 2021), Apple M1 Pro, 32 GB Ram

Results:
-------
```
python3 benchmark_vpdq_index.py brute_force -f 500 -v 20  -q 1000
build: 0.0000s
query: 7.1112s
  Per query: 7.1112ms

% python3 benchmark_vpdq_index.py flat -f 500 -v 20 -q 1000
build: 0.0130s
query: 0.0157s
  Per query: 0.0157ms


% python3 benchmark_vpdq_index.py signal_type -f 500 -v 2000 -q 10000
Generating data...
Generating data: 8.7703s
build: 16.8385s
query: 5.8271s
  Per query: 0.5827ms

% python3 benchmark_vpdq_index.py flat -f 500 -v 2000 -q 10000
Generating data...
Generating data: 9.0299s
build: 1.1329s
query: 5.4447s
  Per query: 0.5445ms


% python3 benchmark_vpdq_index.py flat -f 500 -v 2000 -q 100000
Generating data...
Generating data: 8.9390s
build: 1.1269s
Generating queries...
Generating queries: 1.2121s
query: 56.0504s
  Per query: 0.5605ms
```
