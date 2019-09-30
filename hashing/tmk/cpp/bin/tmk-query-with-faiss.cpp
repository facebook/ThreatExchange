// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

/* ----------------------------------------------------------------
java TETagQuery tag-to-details --page-size 10 --hash-dir ./tetmk media_type_long_hash_video

g++ \
  -Xpreprocessor -fopenmp -lomp \
    -O2 -std=c++14 \
    -I. -I./tmk -I./pdq -I../../faiss \
    tmk/bin/tmk-query-with-faiss.cpp \
    -o tmk-query-with-faiss \
    -L. -ltmk -L ../../faiss -lfaiss

export DYLD_LIBRARY_PATH=/usr/lib:/usr/local/lib:../../faiss

./tmk-query-with-faiss needles.txt haystack.txt
---------------------------------------------------------------- */

#include <tmk/cpp/algo/tmkfv.h>
#include <tmk/cpp/io/tmkio.h>

#include <IndexIVFPQ.h>
#include <IndexFlat.h>
#include <index_io.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <cmath>
#include <chrono>
#include <map>
#include <set>

using namespace facebook::tmk;
using namespace facebook::tmk::algo;

// These are the minimum-possible values. They result in the most expensive
// possible scan through input video-data. Command-line flags --c1 and --c2
// can be used for search-pruning. Note that thresholds depend on choice of
// frame-feature algorithm.
#define DEFAULT_LEVEL_1_THRESHOLD -1.0
#define DEFAULT_LEVEL_2_THRESHOLD 0.0

void handleListFileNameOrDie(
    const char* argv0,
    const char* listFileName,
    std::map<std::string, std::shared_ptr<TMKFeatureVectors>>&
        metadataToFeatures);

void handleListFpOrDie(
    const char* argv0,
    FILE* listFp,
    std::map<std::string, std::shared_ptr<TMKFeatureVectors>>&
        metadataToFeatures);

void handleTmkFileNameOrDie(
    const char* argv0,
    const char* tmkFileName,
    std::map<std::string, std::shared_ptr<TMKFeatureVectors>>&
        metadataToFeatures);

// ================================================================
void usage(char* argv0, int exit_rc) {
  FILE* fp = (exit_rc == 0) ? stdout : stderr;
  fprintf(
      fp,
      "Usage: %s [options] [needles file name] {haystack file name}\n",
      argv0);
  fprintf(
      fp,
      "Needles file and haystack file should each contain .tmk file names,\n"
      "one per line. Then the haystack .tmk files are loaded into memory.\n"
      "Then each needle .tmk file is queried against the haystack, and all\n"
      "matches within specified level-1/level-2 thresholds are printed.\n");
  fprintf(fp, "Options:\n");
  fprintf(fp, "-v|--verbose: Be more verbose.\n");
  fprintf(
      fp,
      "--c1 {x}: Level-1 threshold: default %.3f.\n",
      DEFAULT_LEVEL_1_THRESHOLD);
  fprintf(
      fp,
      "--c2 {y}: Level-2 threshold: default %.3f.\n",
      DEFAULT_LEVEL_2_THRESHOLD);
  exit(exit_rc);
}

// ================================================================
int main(int argc, char** argv) {
  bool verbose = false;
  float c1 = DEFAULT_LEVEL_1_THRESHOLD;
  float c2 = DEFAULT_LEVEL_2_THRESHOLD;
  int i, j;

  int argi = 1;
  while ((argi < argc) && argv[argi][0] == '-') {
    char* flag = argv[argi++];
    if (!strcmp(flag, "-h") || !strcmp(flag, "--help")) {
      usage(argv[0], 0);
    } else if (!strcmp(flag, "-v") || !strcmp(flag, "--verbose")) {
      verbose = true;

    } else if (!strcmp(flag, "--c1")) {
      if (argi >= argc) {
        usage(argv[0], 1);
      }
      if (sscanf(argv[argi], "%f", &c1) != 1) {
        usage(argv[0], 1);
      }
      argi++;
    } else if (!strcmp(flag, "--c2")) {
      if (argi >= argc) {
        usage(argv[0], 1);
      }
      if (sscanf(argv[argi], "%f", &c2) != 1) {
        usage(argv[0], 1);
      }
      argi++;

    } else {
      usage(argv[0], 1);
    }
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // LOAD FEATURES

  std::chrono::time_point<std::chrono::system_clock> startLoad =
      std::chrono::system_clock::now();

  std::map<std::string, std::shared_ptr<TMKFeatureVectors>>
      needlesMetadataToFeatures;
  std::map<std::string, std::shared_ptr<TMKFeatureVectors>>
      haystackMetadataToFeatures;

  if ((argc - argi) == 1) {
    handleListFpOrDie(argv[0], stdin, needlesMetadataToFeatures);
    handleListFileNameOrDie(argv[0], argv[argi], haystackMetadataToFeatures);
  } else if ((argc - argi) == 2) {
    handleListFileNameOrDie(argv[0], argv[argi], needlesMetadataToFeatures);
    handleListFileNameOrDie(
        argv[0], argv[argi + 1], haystackMetadataToFeatures);
  } else {
    usage(argv[0], 1);
    exit(1);
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // POPULATE FAISS INDEX WITH TMK LEVEL-1 FEATURES

  const auto& firstFV = haystackMetadataToFeatures.begin()->second;
  if (firstFV == NULL) {
    fprintf(stderr, "Empty haystack: cannot find dimension.\n");
    exit(1);
  }
  int vector_dimension = firstFV->getFrameFeatureDimension();

  size_t num_database_vectors = haystackMetadataToFeatures.size();

  // Make the index object and train it
  faiss::IndexFlatL2 coarse_quantizer(vector_dimension);

  // A reasonable number of centroids to index num_database_vectors vectors
  int num_centroids = int(4 * sqrt(num_database_vectors));
  if (num_centroids > num_database_vectors) {
    num_centroids = num_database_vectors;
  }
  printf("VECTOR_DIMENSION     %d\n", (int)vector_dimension);
  printf("NUM_DATABASE_VECTORS %d\n", (int)num_database_vectors);
  printf("NUM_CENTROIDS        %d\n", (int)num_centroids);

  // The coarse quantizer should not be deallocated before the index.
  // 4 = number of bytes per code (vector_dimension must be a multiple of this)
  // 8 = number of bits per sub-code (almost always 8)
  faiss::IndexIVFPQ faiss_index(&coarse_quantizer, vector_dimension, num_centroids, 4, 8);
  faiss_index.verbose = verbose;

  // Really a vector of vectors but for FAISS it's one long vector
  std::vector<float> database(num_database_vectors * vector_dimension);
  i = 0;
  for (const auto& it : haystackMetadataToFeatures) {
    const auto& haystackFV = it.second;
    const std::vector<float>& haystack_vector = haystackFV->getPureAverageFeature();
    for (j = 0; j < vector_dimension; j++) {
      database[i * vector_dimension + j] = haystack_vector[j];
    }
    i++;
  }

  // Train the quantizer, using the database
  printf("Start training the quantizer:\n");
  faiss_index.train(num_database_vectors, database.data());
  printf("End training the quantizer.\n");

  faiss_index.add(num_database_vectors, database.data());

  printf("imbalance factor: %g\n", faiss_index.invlists->imbalance_factor());

  std::vector<std::string> haystack_filenames_as_vector(haystackMetadataToFeatures.size());
  std::vector<std::string> needles_filenames_as_vector(needlesMetadataToFeatures.size());
  i = 0;
  for (const auto& it : haystackMetadataToFeatures) {
    haystack_filenames_as_vector[i] = it.first;
    i++;
  }
  i = 0;
  for (const auto& it : needlesMetadataToFeatures) {
    needles_filenames_as_vector[i] = it.first;
    i++;
  }

  std::chrono::time_point<std::chrono::system_clock> endLoad =
      std::chrono::system_clock::now();
  std::chrono::duration<double> loadSeconds = endLoad - startLoad;
  if (verbose) {
    printf("LOAD SECONDS   = %.3lf\n", loadSeconds.count());
    printf("NEEDLES COUNT  = %d\n", (int)needlesMetadataToFeatures.size());
    printf("HAYSTACK COUNT = %d\n", (int)haystackMetadataToFeatures.size());
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // SANITY-CHECK (OMITTABLE FOR PRODUCTION ONCE WE SETTLE ON ONE FRAMEWISE
  // ALGORITHM)
  std::chrono::time_point<std::chrono::system_clock> startCheck =
      std::chrono::system_clock::now();
  for (const auto& it1 : needlesMetadataToFeatures) {
    const std::string& metadata1 = it1.first;
    std::shared_ptr<TMKFeatureVectors> pfv1 = it1.second;

    for (const auto& it2 : haystackMetadataToFeatures) {
      const std::string& metadata2 = it2.first;
      std::shared_ptr<TMKFeatureVectors> pfv2 = it2.second;

      if (!TMKFeatureVectors::areCompatible(*pfv1, *pfv2)) {
        fprintf(
            stderr,
            "%s: immiscible provenances:\n%s\n%s\n",
            argv[0],
            metadata1.c_str(),
            metadata2.c_str());
        exit(1);
      }
    }
  }

  std::chrono::time_point<std::chrono::system_clock> endCheck =
      std::chrono::system_clock::now();
  std::chrono::duration<double> checkSeconds = endCheck - startCheck;
  if (verbose) {
    printf("\n");
    printf("CHECK SECONDS = %.3lf\n", checkSeconds.count());
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // SAVE OFF THE INDEX
  // const char *index_output_file_name = "/tmp/index_trained.faissindex";
  // printf("Storing the pre-trained index to %s\n", index_output_file_name);
  // write_index(&faiss_index, index_output_file_name);

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // QUERY USING FAISS
  std::chrono::time_point<std::chrono::system_clock> startQuery =
      std::chrono::system_clock::now();

  size_t num_queries = needlesMetadataToFeatures.size();
  // Really a vector of vectors but for FAISS it's one long vector
  std::vector<float> queries(num_queries * vector_dimension);
  i = 0;
  for (const auto& it : needlesMetadataToFeatures) {
    const auto& needleFV = it.second;
    const std::vector<float>& needle_vector = needleFV->getPureAverageFeature();
    for (j = 0; j < vector_dimension; j++) {
      queries[i * vector_dimension + j] = needle_vector[j];
    }
    i++;
  }

  int k = 5;
  printf("Searching for the %d nearest neighbors\n", k);

  std::vector<faiss::Index::idx_t> nearest_neighbor_indices(k * num_queries);
  std::vector<float> nearest_neighbor_distances(k * num_queries);

  faiss_index.search(
    num_queries,
    queries.data(),
    k,
    nearest_neighbor_distances.data(),
    nearest_neighbor_indices.data()
  );

  std::chrono::time_point<std::chrono::system_clock> endQuery =
      std::chrono::system_clock::now();
  std::chrono::duration<double> querySeconds = endQuery - startQuery;
  if (verbose) {
    printf("\n");
    printf("QUERY SECONDS = %.6lf\n", querySeconds.count());
    printf(
        "MEAN QUERY SECONDS = %.6lf\n",
        querySeconds.count() / needlesMetadataToFeatures.size());
  }

  printf("Query results (vector IDs, then distances):\n");
  printf("(Note that the nearest neighbor is not always at distance 0 due to quantization errors.)\n");

  for (i = 0; i < num_queries; i++) {
    const std::string& needleFilename = needles_filenames_as_vector[i];
    const std::shared_ptr<TMKFeatureVectors> pneedleFV = needlesMetadataToFeatures.at(needleFilename);
    printf("Query %2d %s:\n", i, needleFilename.c_str());

    for (int j = 0; j < k; j++) {
      int nnidx = (int)nearest_neighbor_indices[i*k+j];
      if (nnidx < 0) { // -1 for ... I'm not yet sure why.
        continue;
      }
      float nndist = nearest_neighbor_distances[i*k+j];
      const std::string& haystackFilename = haystack_filenames_as_vector[nnidx];
      const std::shared_ptr<TMKFeatureVectors> phaystackFV = haystackMetadataToFeatures.at(haystackFilename);

      float s1 = TMKFeatureVectors::computeLevel1Score(*pneedleFV, *phaystackFV);
      float s2 = TMKFeatureVectors::computeLevel2Score(*pneedleFV, *phaystackFV);

      printf("  distance %.6f L1 %.6f L2 %.6f metadata %s\n",
        nndist,
        s1,
        s2,
        haystackFilename.c_str());
    }
    printf("\n");
  }

  return 0;
}

// ----------------------------------------------------------------
void handleListFileNameOrDie(
    const char* argv0,
    const char* listFileName,
    std::map<std::string, std::shared_ptr<TMKFeatureVectors>>&
        metadataToFeatures) {
  FILE* fp = fopen(listFileName, "r");
  if (fp == nullptr) {
    perror("fopen");
    fprintf(
        stderr, "%s: could not open \"%s\" for read.\n", argv0, listFileName);
    exit(1);
  }

  handleListFpOrDie(argv0, fp, metadataToFeatures);

  fclose(fp);
}

// ----------------------------------------------------------------
void handleListFpOrDie(
    const char* argv0,
    FILE* listFp,
    std::map<std::string, std::shared_ptr<TMKFeatureVectors>>&
        metadataToFeatures) {
  char* tmkFileName = nullptr;
  size_t linelen = 0;
  while ((ssize_t)(linelen = getline(&tmkFileName, &linelen, listFp)) != -1) {
    // Chomp
    if (linelen > 0) {
      if (tmkFileName[linelen - 1] == '\n') {
        tmkFileName[linelen - 1] = 0;
      }
    }
    handleTmkFileNameOrDie(argv0, tmkFileName, metadataToFeatures);
  }
}

// ----------------------------------------------------------------
void handleTmkFileNameOrDie(
    const char* argv0,
    const char* tmkFileName,
    std::map<std::string, std::shared_ptr<TMKFeatureVectors>>&
        metadataToFeatures) {
  std::shared_ptr<TMKFeatureVectors> pfv =
      TMKFeatureVectors::readFromInputFile(tmkFileName, argv0);

  if (pfv == nullptr) {
    fprintf(stderr, "%s: failed to read \"%s\".\n", argv0, tmkFileName);
    exit(1);
  }

  pfv->L2NormalizePureAverageFeature();

  metadataToFeatures[std::string(tmkFileName)] = pfv;
}
