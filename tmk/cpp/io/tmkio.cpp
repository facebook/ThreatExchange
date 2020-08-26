// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

// ================================================================
// Methods for reading/writing TMK file formats: .vstr/.feat/.tmk file
// headers, RGB frame-raster contents, and float-array contents.
// ================================================================

#include <tmk/cpp/io/tmkio.h>

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

namespace facebook {
namespace tmk {
namespace io {

// ----------------------------------------------------------------
FILE* openFileOrDie(const char* filename, const char* mode, const char* argv0) {
  FILE* fp = fopen(filename, mode);
  if (fp == nullptr) {
    perror("fopen");
    fprintf(
        stderr,
        "%s: could not open \"%s\" for mode \"%s\".\n",
        argv0,
        filename,
        mode);
    exit(1);
  }
  return fp;
}

// ----------------------------------------------------------------
TMKFramewiseAlgorithm algoFromMagic(char magic[4]) {
  if (!memcmp(&magic[0], PDQ_FLOAT_ALGO_MAGIC, TMK_MAGIC_LENGTH)) {
    return TMKFramewiseAlgorithm::PDQ_FLOAT;
  } else {
    return TMKFramewiseAlgorithm::UNRECOGNIZED;
  }
}

// ----------------------------------------------------------------
TMKFramewiseAlgorithm
algoFromMagicOrDie(char* argv0, char magic[4], char* fromFileName) {
  TMKFramewiseAlgorithm algorithm = algoFromMagic(magic);
  if (algorithm == TMKFramewiseAlgorithm::UNRECOGNIZED) {
    reportUnrecognizedAlgorithmMagic(argv0, magic, fromFileName);
    exit(1);
  }
  return algorithm;
}

// ----------------------------------------------------------------
void reportUnrecognizedAlgorithmMagic(
    char* argv0,
    char magic[4],
    char* fromFileName) {
  fprintf(
      stderr,
      "%s: unrecognized algorithm %c%c%c%c (%02x%02x%02x%02x) in \"%s\".\n",
      argv0,
      makePrintable(magic[0]),
      makePrintable(magic[1]),
      makePrintable(magic[2]),
      makePrintable(magic[3]),
      magic[0],
      magic[1],
      magic[2],
      magic[3],
      fromFileName);
}

// ----------------------------------------------------------------
bool algoToMagic(
    TMKFramewiseAlgorithm algorithm,
    char magic[TMK_MAGIC_LENGTH]) {
  bool rv = false;
  switch (algorithm) {
    case TMKFramewiseAlgorithm::PDQ_FLOAT:
      memcpy(&magic[0], PDQ_FLOAT_ALGO_MAGIC, TMK_MAGIC_LENGTH);
      rv = true;
      break;
    default:
      break;
  }
  return rv;
}

// ----------------------------------------------------------------
TMKFramewiseAlgorithm algoFromLowercaseName(std::string name) {
  if (name == "pdqf") {
    return TMKFramewiseAlgorithm::PDQ_FLOAT;
  } else if (name == "pdqfloat") {
    return TMKFramewiseAlgorithm::PDQ_FLOAT;
  } else {
    return TMKFramewiseAlgorithm::UNRECOGNIZED;
  }
}

// ----------------------------------------------------------------
std::string algorithmToName(TMKFramewiseAlgorithm algorithm) {
  switch (algorithm) {
    case TMKFramewiseAlgorithm::PDQ_FLOAT:
      return std::string("PDQF");
      break;
    default:
      return std::string("????");
      break;
  }
}

// ----------------------------------------------------------------
bool readDecodedVideoStreamFileHeader(
    FILE* fp,
    DecodedVideoStreamFileHeader* pheader,
    const char* programName) {
  size_t rc = fread(pheader, sizeof(*pheader), 1, fp);
  if (rc != 1) {
    perror("fread");
    fprintf(
        stderr,
        "%s: failed to read decodedVideoStreamFileHeader.\n",
        programName);
    return false;
  }

  if (!checkMagic(
          pheader->projectMagic, (char*)TMK_PROJECT_MAGIC, programName)) {
    return false;
  }
  if (!checkMagic(
          pheader->fileTypeMagic, (char*)VSTR_FILETYPE_MAGIC, programName)) {
    return false;
  }

  return true;
}

// ----------------------------------------------------------------
bool readFrameFeaturesFileHeader(
    FILE* fp,
    FrameFeaturesFileHeader* pheader,
    TMKFramewiseAlgorithm& algorithm,
    const char* programName) {
  size_t rc = fread(pheader, sizeof(*pheader), 1, fp);
  if (rc != 1) {
    perror("fread");
    fprintf(
        stderr,
        "%s: failed to read decodedVideoStreamFileHeader.\n",
        programName);
    return false;
  }

  if (!checkMagic(
          pheader->projectMagic, (char*)TMK_PROJECT_MAGIC, programName)) {
    return false;
  }
  if (!checkMagic(
          pheader->fileTypeMagic, (char*)FEAT_FILETYPE_MAGIC, programName)) {
    return false;
  }

  algorithm = algoFromMagic(pheader->frameFeatureAlgorithmMagic);

  return true;
}

// ----------------------------------------------------------------
bool readFeatureVectorFileHeader(
    FILE* fp,
    FeatureVectorFileHeader* pheader,
    TMKFramewiseAlgorithm& algorithm,
    const char* programName) {
  size_t rc = fread(pheader, sizeof(*pheader), 1, fp);
  if (rc != 1) {
    perror("fread");
    fprintf(
        stderr,
        "%s: failed to read decodedVideoStreamFileHeader.\n",
        programName);
    return false;
  }

  if (!checkMagic(
          pheader->projectMagic, (char*)TMK_PROJECT_MAGIC, programName)) {
    return false;
  }
  if (!checkMagic(
          pheader->fileTypeMagic, (char*)FVEC_FILETYPE_MAGIC, programName)) {
    return false;
  }

  algorithm = algoFromMagic(pheader->frameFeatureAlgorithmMagic);

  return true;
}

// ----------------------------------------------------------------
bool writeDecodedVideoStreamFileHeader(
    FILE* fp,
    int frameHeight,
    int frameWidth,
    int framesPerSecond,
    const char* programName) {
  DecodedVideoStreamFileHeader header;
  memset(&header, 0, sizeof(header));

  for (int i = 0; i < TMK_MAGIC_LENGTH; i++) {
    header.projectMagic[i] = TMK_PROJECT_MAGIC[i];
    header.fileTypeMagic[i] = VSTR_FILETYPE_MAGIC[i];
  }
  header.frameHeight = frameHeight;
  header.frameWidth = frameWidth;
  header.framesPerSecond = framesPerSecond;

  size_t rc = fwrite(&header, sizeof(header), 1, fp);
  if (rc != 1) {
    perror("fwrite");
    fprintf(
        stderr,
        "%s: failed to write decodedVideoStreamFileHeader.\n",
        programName);
    return false;
  }
  return true;
}

// ----------------------------------------------------------------
bool writeFrameFeaturesFileHeader(
    FILE* fp,
    TMKFramewiseAlgorithm algorithm,
    int frameFeatureDimension,
    int framesPerSecond,
    const char* programName) {
  FrameFeaturesFileHeader header;
  memset(&header, 0, sizeof(header));

  for (int i = 0; i < TMK_MAGIC_LENGTH; i++) {
    header.projectMagic[i] = TMK_PROJECT_MAGIC[i];
    header.fileTypeMagic[i] = FEAT_FILETYPE_MAGIC[i];
  }

  char algorithmMagic[TMK_MAGIC_LENGTH];
  if (!algoToMagic(algorithm, algorithmMagic)) {
    fprintf(
        stderr,
        "%s: Internal coding error: algorithm %d unmapped.\n",
        programName,
        (int)algorithm);
    return false;
  }
  memcpy(
      &header.frameFeatureAlgorithmMagic[0],
      &algorithmMagic[0],
      TMK_MAGIC_LENGTH);

  header.frameFeatureDimension = frameFeatureDimension;
  header.framesPerSecond = framesPerSecond;

  size_t rc = fwrite(&header, sizeof(header), 1, fp);
  if (rc != 1) {
    perror("fwrite");
    fprintf(
        stderr, "%s: failed to write frameFeaturesFileHeader.\n", programName);
    return false;
  }
  return true;
}

// ----------------------------------------------------------------
bool writeFeatureVectorFileHeader(
    FILE* fp,
    TMKFramewiseAlgorithm algorithm,
    int framesPerSecond,
    int numPeriods, // a.k.a. P
    int numFourierCoefficients, // a.k.a m
    int frameFeatureDimension, // a.k.a d
    int frameFeatureCount,
    const char* programName) {
  FeatureVectorFileHeader header;
  memset(&header, 0, sizeof(header));

  for (int i = 0; i < TMK_MAGIC_LENGTH; i++) {
    header.projectMagic[i] = TMK_PROJECT_MAGIC[i];
    header.fileTypeMagic[i] = FVEC_FILETYPE_MAGIC[i];
  }

  char algorithmMagic[TMK_MAGIC_LENGTH];
  if (!algoToMagic(algorithm, algorithmMagic)) {
    fprintf(
        stderr,
        "%s: Internal coding error: algorithm %d unmapped.\n",
        programName,
        (int)algorithm);
    return false;
  }
  memcpy(
      &header.frameFeatureAlgorithmMagic[0],
      &algorithmMagic[0],
      TMK_MAGIC_LENGTH);

  header.framesPerSecond = framesPerSecond;
  header.numPeriods = numPeriods;
  header.numFourierCoefficients = numFourierCoefficients;
  header.frameFeatureDimension = frameFeatureDimension;
  header.frameFeatureCount = frameFeatureCount;
  size_t rc = fwrite(&header, sizeof(header), 1, fp);
  if (rc != 1) {
    perror("fwrite");
    fprintf(
        stderr, "%s: failed to write featureVectorFileHeader.\n", programName);
    return false;
  }
  return true;
}

// ----------------------------------------------------------------
char makePrintable(char c) {
  return isprint(c) ? c : '?';
}

// ----------------------------------------------------------------
bool checkMagic(
    char actual[TMK_MAGIC_LENGTH],
    char* expected,
    const char* programName) {
  bool ok = true;
  if (strlen(expected) != TMK_MAGIC_LENGTH) {
    ok = false;
  } else {
    for (int i = 0; i < TMK_MAGIC_LENGTH; i++) {
      if (actual[i] != expected[i]) {
        ok = false;
        break;
      }
    }
  }

  if (!ok) {
    fprintf(
        stderr,
        "%s: got magic number %c%c%c%c (%02x%02x%02x%02x); "
        "expected %c%c%c%c (%02x%02x%02x%02x).\n",
        programName,
        makePrintable(actual[0]),
        makePrintable(actual[1]),
        makePrintable(actual[2]),
        makePrintable(actual[3]),
        actual[0],
        actual[1],
        actual[2],
        actual[3],
        makePrintable(expected[0]),
        makePrintable(expected[1]),
        makePrintable(expected[2]),
        makePrintable(expected[3]),
        expected[0],
        expected[1],
        expected[2],
        expected[3]);
  }

  return ok;
}

// ----------------------------------------------------------------
bool readRGBTriples(
    unsigned char* buffer,
    int height,
    int width,
    FILE* fp,
    bool& eof) {
  eof = false;
  int numRGBTriples = height * width;

  size_t fread_rc = fread(buffer, 3, numRGBTriples, fp);
  if (fread_rc == 0) {
    eof = true;
    return false;
  }
  if (fread_rc != numRGBTriples) {
    perror("fread");
    fprintf(
        stderr,
        "Expected %d RGB triples; got %d\n",
        numRGBTriples,
        (int)fread_rc);
    return false;
  }
  return true;
}

// ----------------------------------------------------------------
bool readFloatVector(std::vector<float>& vector, FILE* fp, bool& eof) {
  eof = false;

  size_t fread_rc = fread(vector.data(), sizeof(float), vector.size(), fp);
  if (fread_rc == 0) {
    eof = true;
    return false;
  }
  if (fread_rc != vector.size()) {
    perror("fread");
    fprintf(
        stderr,
        "Expected %d floats; got %d\n",
        (int)vector.size(),
        (int)fread_rc);
    return false;
  }
  return true;
}

// ----------------------------------------------------------------
bool writeFloatVector(const std::vector<float>& vector, FILE* fp) {
  size_t fwrite_rc = fwrite(vector.data(), sizeof(float), vector.size(), fp);
  if (fwrite_rc != vector.size()) {
    perror("fwrite");
    fprintf(
        stderr,
        "Expected %d floats; got %d\n",
        (int)vector.size(),
        (int)fwrite_rc);
    return false;
  }
  return true;
}

// ----------------------------------------------------------------
bool readIntVector(std::vector<int>& vector, FILE* fp) {
  size_t fread_rc = fread(vector.data(), sizeof(int), vector.size(), fp);
  if (fread_rc == 0) {
    return false;
  }
  if (fread_rc != vector.size()) {
    perror("fread");
    fprintf(
        stderr,
        "Expected %d ints; got %d\n",
        (int)vector.size(),
        (int)fread_rc);
    return false;
  }
  return true;
}

// ----------------------------------------------------------------
bool writeIntVector(const std::vector<int>& vector, FILE* fp) {
  size_t fwrite_rc = fwrite(vector.data(), sizeof(int), vector.size(), fp);
  if (fwrite_rc != vector.size()) {
    perror("fwrite");
    fprintf(
        stderr,
        "Expected %d ints; got %d\n",
        (int)vector.size(),
        (int)fwrite_rc);
    return false;
  }
  return true;
}

} // namespace io
} // namespace tmk
} // namespace facebook
