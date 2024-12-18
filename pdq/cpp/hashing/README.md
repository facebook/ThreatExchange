# Benchmark for hashing
Benchmark for PDQ hashing on images

## Instructions
```
cd pdq/cpp
make bin/benchmark-photo-hasher
./benchmark-photo-hasher
```

Help command:
```
$ ./benchmark-query -h
Usage: ./benchmark-photo-hasher [options] folder_path
Options:
  -v               Verbose output
  -n N             Total number of hashes to generate, can be more or less than the number of images in the folder
                           (default: 0, meaning generate one hash for each image in the folder)
  --dihedral       Compute dihedral versions of the hashes (default: false)
```

Note: if `-n N` is larger than the number of images in the folder, the benchmark will loop over each image in the folder until `N` hashes have been generated

## Results
Ran on Ubuntu 24.04.1 LTS, Intel Core i7-14700KF with 20 cores, 28 threads, 64GB RAM

```
$ ./benchmark-photo-hasher ../data/reg-test-input/dih/
PHOTO COUNT:               8
ERROR COUNT:               0
TIME SPENT HASHING PHOTOS (SECONDS):     0.015171
PHOTOS HASHED PER SECOND:   527.324158
TIME SPENT READING PHOTOS (SECONDS):        0.299410
PHOTOS READ PER SECOND:     26.719229

$ ./benchmark-photo-hasher -n 10 ../data/reg-test-input/dih/
PHOTO COUNT:               10
ERROR COUNT:               0
TIME SPENT HASHING PHOTOS (SECONDS):     0.018181
PHOTOS HASHED PER SECOND:   550.028442
TIME SPENT READING PHOTOS (SECONDS):        0.334852
PHOTOS READ PER SECOND:     29.863914

$ ./benchmark-photo-hasher -n 100 ../data/reg-test-input/dih/
PHOTO COUNT:               100
ERROR COUNT:               0
TIME SPENT HASHING PHOTOS (SECONDS):     0.182545
PHOTOS HASHED PER SECOND:   547.810364
TIME SPENT READING PHOTOS (SECONDS):        2.841218
PHOTOS READ PER SECOND:     35.196167

$ ./benchmark-photo-hasher -n 1000 ../data/reg-test-input/dih/
PHOTO COUNT:               1000
ERROR COUNT:               0
TIME SPENT HASHING PHOTOS (SECONDS):     1.767847
PHOTOS HASHED PER SECOND:   565.659729
TIME SPENT READING PHOTOS (SECONDS):        27.135609
PHOTOS READ PER SECOND:     36.851948
```