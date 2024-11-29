# Benchmark for index
Benchmark PDQ CPP brute force queries and mutually-indexed hashing queries

Needles are target hashes
Haystack count is all hashes stored in the index

## Instructions
```
cd pdq/cpp
make bin/benchmark-query
./benchmark-query
```

Help command:
```
$ ./benchmark-query -h
Usage: ./benchmark-query [options]
Options:
  -v               Verbose output
  --seed N         Random seed (default: 41)
  -q N             Number of queries to run (default: 1000)
  -b N             Number of PDQ hashes to query against (default: 10000)
  -d N             Maximum Hamming distance for matches (default: 31)
  -m               Method for querying (default: linear), Available: linear, mih
```

## Results
Ran on Ubuntu 24.04.1 LTS, Intel Core i7-14700KF with 20 cores, 28 threads, 64GB RAM

```
$ ./benchmark-query -m linear
METHOD: Linear query
QUERY COUNT:             1000
INDEX COUNT:             10000
TOTAL MATCH COUNT:       1000
TOTAL QUERY SECONDS:     0.258911
SECONDS PER QUERY:       0.000259

$ ./benchmark-query -m mih
METHOD: Mutually-indexed hashing query
INDEX BUILD SECONDS:     0.053034
QUERY COUNT:             1000
INDEX COUNT:             10000
TOTAL MATCH COUNT:       1000
TOTAL QUERY SECONDS:     0.030150
SECONDS PER QUERY:       0.000030

/benchmark-query -m linear -d 63
METHOD: Linear query
QUERY COUNT:             1000
INDEX COUNT:             10000
TOTAL MATCH COUNT:       1000
TOTAL QUERY SECONDS:     0.262353
SECONDS PER QUERY:       0.000262

$ ./benchmark-query -m mih -d 63
METHOD: Mutually-indexed hashing query
INDEX BUILD SECONDS:     0.039096
QUERY COUNT:             1000
INDEX COUNT:             10000
TOTAL MATCH COUNT:       1000
TOTAL QUERY SECONDS:     0.902643
SECONDS PER QUERY:       0.000903

$ ./benchmark-query -m linear -b 50000 -q 5000
METHOD: Linear query
QUERY COUNT:             5000
INDEX COUNT:             50000
TOTAL MATCH COUNT:       5000
TOTAL QUERY SECONDS:     6.085275
SECONDS PER QUERY:       0.001217

$ ./benchmark-query -m mih -b 50000 -q 5000
METHOD: Mutually-indexed hashing query
INDEX BUILD SECONDS:     0.244458
QUERY COUNT:             5000
INDEX COUNT:             50000
TOTAL MATCH COUNT:       5000
TOTAL QUERY SECONDS:     0.501590
SECONDS PER QUERY:       0.000100

```