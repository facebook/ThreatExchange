// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#ifndef HASHIO_H
#define HASHIO_H

#include <istream>

#include <pdq/cpp/common/pdqhashtypes.h>

#include <stdio.h>
#include <string>
#include <vector>

namespace facebook {
namespace pdq {
namespace io {

// ----------------------------------------------------------------
// Hashes with metadata
//
// If zero filenames are provided, stdin is read.  Files should have one
// hex-formatted 256-bit hash per line, optionally prefixed by "hash=". If
// a comma and other text follows the hash, it is used as metadata; else,
// a counter is used as the metadata.
//
// Example:
// f8f8f0cce0f4e84d0e370a22028f67f0b36e2ed596623e1d33e6339c4e9c9b22
// b0a10efd71cc3f429413d48d0ffffe12e34e0e17ada952a9d29684210aa9e5af
// adad5a64b5a142e55362a09057dacd5ae63b847fc23794b766b319361fc93188
// a5f4a457a48995e8c9065c275aaa5498b61ba4bdf8fcf80387c32f8b0bfc4f05
// f8f80f31e0f417b00e37f5cd028f980fb36ed02a9662c1e233e6cc634e9c64dd
// 8dad2599b1a1bd1853625f6553da32a1e63b7280c2374b4866b366c91bc9ce77
// f0a1f102f1dcc0bd9c5309720fff018de34ef1e8ada9a956d2967ade0ea91a50
// a5f05ba8a4896a17c106a3da5aaaab07b61b5b42f8fc07fc83c3d0740bfcb0fa
//
// Example:
// f8f8f0cce0f4e84d0e370a22028f67f0b36e2ed596623e1d33e6339c4e9c9b22,file1.jpg
// b0a10efd71cc3f429413d48d0ffffe12e34e0e17ada952a9d29684210aa9e5af,file2.jpg
// adad5a64b5a142e55362a09057dacd5ae63b847fc23794b766b319361fc93188,file3.jpg
// a5f4a457a48995e8c9065c275aaa5498b61ba4bdf8fcf80387c32f8b0bfc4f05,file4.jpg
// f8f80f31e0f417b00e37f5cd028f980fb36ed02a9662c1e233e6cc634e9c64dd,file5.jpg
// 8dad2599b1a1bd1853625f6553da32a1e63b7280c2374b4866b366c91bc9ce77,file6.jpg
// f0a1f102f1dcc0bd9c5309720fff018de34ef1e8ada9a956d2967ade0ea91a50,file7.jpg
// a5f05ba8a4896a17c106a3da5aaaab07b61b5b42f8fc07fc83c3d0740bfcb0fa,file8.jpg
//
// Example:
// hash=f8f8...9b22,norm=128,delta=0,quality=100,filename=file1.jpg
// hash=b0a1...e5af,norm=128,delta=124,quality=100,filename=file2.jpg
// hash=adad...3188,norm=128,delta=122,quality=100,filename=file3.jpg
// hash=a5f4...4f05,norm=128,delta=118,quality=100,filename=file4.jpg
// hash=f8f8...64dd,norm=128,delta=124,quality=100,filename=file5.jpg
// hash=8dad...ce77,norm=128,delta=122,quality=100,filename=file6.jpg
// hash=f0a1...1a50,norm=128,delta=124,quality=100,filename=file7.jpg
// hash=a5f0...b0fa,norm=128,delta=124,quality=100,filename=file8.jpg

bool loadHashAndMetadataFromStream(
    std::istream& in,
    facebook::pdq::hashing::Hash256& hash,
    std::string& metadata,
    // Used in case metadata is absent. Please pass in an incremented counter:
    int counter);

void loadHashesAndMetadataFromStream(
    std::istream& in,
    std::vector<std::pair<facebook::pdq::hashing::Hash256, std::string>>&
        vector_of_pairs);

// On file-read error, returns false.
bool loadHashesAndMetadataFromFile(
    const char* filename,
    std::vector<std::pair<facebook::pdq::hashing::Hash256, std::string>>&
        vector_of_pairs);

// On any file-read error, returns false. If the filenames array
// is zero-length, reads from stdin, else reads from all files.
// Analog of Ruby's ARGF.
bool loadHashesAndMetadataFromFiles(
    char** filenames,
    int num_filenames,
    std::vector<std::pair<facebook::pdq::hashing::Hash256, std::string>>&
        vector_of_pairs);

// ----------------------------------------------------------------
// Hashes without metadata
// If there is a hash-file with metadata from which you wish to extract
// only the hashes, you might use sed, or 'mlr --onidx cut -f hash'
// (https://github.com/johnkerl/miller).

// The "...OrDie" functions exit the process on read-failure.
void loadHashesFromFilesOrDie(
    char** filenames,
    int num_filenames,
    std::vector<facebook::pdq::hashing::Hash256>& hashes);

void loadHashesFromFileOrDie(
    const char* filename, std::vector<facebook::pdq::hashing::Hash256>& hashes);

bool loadHashesFromFile(
    const char* filename, std::vector<facebook::pdq::hashing::Hash256>& hashes);

void loadHashesFromStream(
    std::istream& in, std::vector<facebook::pdq::hashing::Hash256>& hashes);

} // namespace io
} // namespace pdq
} // namespace facebook

#endif // HASHIO_H
