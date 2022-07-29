# pytx-vpdq
Benchmark vPDQ implementation in threatexchange library


# Observed Performance
MacBook Pro (16-inch, 2021), Apple M1 Pro, 32 GB Ram

Results:
-------
```
python3 benchmarks/benchmark_vpdq_index.py brute_force -n 500 -v 20  -q 1000
build: 0.0000s
query: 7.0971s
  Per query: 7.0971ms

% python3 benchmarks/benchmark_vpdq_index.py flat -n 500 -v 20 -q 1000
build: 0.0133s
query: 0.0134s
  Per query: 0.0134ms


% python3 benchmarks/benchmark_vpdq_index.py signal_type -n 500 -v 2000 -q 10000
Generating data...
Generating data: 9.1897s
build: 18.9383s
query: 5.9005s
  Per query: 0.5901ms

% python3 benchmarks/benchmark_vpdq_index.py flat -n 500 -v 2000 -q 10000
Generating data...
Generating data: 8.9557s
build: 1.1351s
query: 6.0112s
  Per query: 0.6011ms


% python3 benchmarks/benchmark_vpdq_index.py flat -n 500 -v 2000 -q 100000
Generating data...
Generating data: 8.9286s
build: 1.1083s
Generating queries...
Generating queries: 1.2861s
query: 62.1991s
  Per query: 0.6220ms
```
