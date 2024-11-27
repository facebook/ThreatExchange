# Benchmark for index
Benchmark PDQ CPP brute force queries and mutually-indexed hashing queries

Needles are target hashes
Haystack count is all hashes stored in the index

## Instructions
```
cd pdq/cpp
make bin/benchmark-mih.cpp
./benchmark-mih
```

Help command:
```
$ ./benchmark-mih -h
Usage: ./benchmark-mih [options]
Options:
  -v                    Verbose output
  --no-timings          Disable timing output
  --seed N              Random seed (default: 41)
  --haystack-size N     Number of hashes in haystack (default: 10000)
  --needles-size N      Number of needle hashes (default: 1000)
  --distance N          Maximum Hamming distance (default: 32)
```

## Results
Ran on Ubuntu 24.04.1 LTS, Intel Core i7-14700KF with 20 cores, 28 threads, 64GB RAM

```
$ ./benchmark-mih
BRUTE-FORCE QUERY:
NEEDLE COUNT:               1000
HAYSTACK COUNT:             11000
TOTAL MATCH COUNT:          1000
SECONDS:                    0.311571
SECONDS PER MATCH:          0.000312

MIH QUERY:
NEEDLE COUNT:               1000
HAYSTACK COUNT:             11000
TOTAL MATCH COUNT:          1000
SECONDS:                    0.237358
SECONDS PER MATCH:          0.000237


$ ./benchmark-mih --distance 48
BRUTE-FORCE QUERY:
NEEDLE COUNT:               1000
HAYSTACK COUNT:             11000
TOTAL MATCH COUNT:          1000
SECONDS:                    0.310662
SECONDS PER MATCH:          0.000311

MIH QUERY:
NEEDLE COUNT:               1000
HAYSTACK COUNT:             11000
TOTAL MATCH COUNT:          1000
SECONDS:                    1.196939
SECONDS PER MATCH:          0.001197


$ ./benchmark-mih --haystack-size 100000 --needles-size 5000
BRUTE-FORCE QUERY:
NEEDLE COUNT:               5000
HAYSTACK COUNT:             105000
TOTAL MATCH COUNT:          5000
SECONDS:                    14.809405
SECONDS PER MATCH:          0.002962

MIH QUERY:
NEEDLE COUNT:               5000
HAYSTACK COUNT:             105000
TOTAL MATCH COUNT:          5000
SECONDS:                    5.878446
SECONDS PER MATCH:          0.001176
```