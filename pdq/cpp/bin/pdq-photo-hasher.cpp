// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

#include <pdq/cpp/io/pdqio.h>
#include <stdlib.h>
#include <string.h>
#include <stdexcept>

// ================================================================
// Ops/demo tool for computing PDQ hashes of image files (JPEG, PNG, etc.)
// ================================================================

using namespace facebook::pdq::hashing;

static void process_file(
    char* argv0,
    char* filename,
    bool do_pdqhash,
    bool do_pdqdih,
    bool do_pdqdih_across,
    bool do_detailed_output,
    bool keep_going_after_errors,
    int num_pdqhash,
    Hash256& pdqhash_prev,
    bool& had_error);

// ----------------------------------------------------------------
static void usage(char* argv0, int rc) {
  FILE* fp = (rc == 0) ? stdout : stderr;
  fprintf(fp, "Usage: %s [options] {one or more filenames}\n", argv0);
  fprintf(fp, "Supported filetypes are JPEG and PNG.\n");
  fprintf(fp, "\n");
  fprintf(fp, "Options:\n");
  fprintf(fp, "-i|--files-on-stdin: Take filenames from stdin, in which\n");
  fprintf(fp, "  case there must be no filenames on the command line.\n");
  fprintf(
      fp,
      "-d|--details: Print norm, delta, etc; else print just hash, "
      "quality, and filename.\n");
  fprintf(fp, "--pdqdih: Print all 8 dihedral-transform hashes.\n");
  fprintf(
      fp,
      "--pdqdih-across: Print all 8 dihedral-transform hashes, all "
      "on one line.\n");
  fprintf(
      fp,
      "-k: Continue to next image after image errors, but still exit "
      "1 afterward.\n");
  fprintf(fp, "--info: show information about the image-decoder library.\n");
  exit(rc);
}

// ----------------------------------------------------------------
int main(int argc, char* argv[]) {
  bool files_on_stdin = false;
  bool do_pdqhash = true;
  bool do_pdqdih = false;
  bool do_pdqdih_across = false;
  bool do_detailed_output = false;
  bool keep_going_after_errors = false;

  // Parse command-line flags. I'm explicitly not using gflags or other such
  // libraries, to minimize the number of external dependencies for this
  // project.
  int argi = 1;
  for (; argi < argc; argi++) {
    if (argv[argi][0] != '-') {
      break;
    }

    if (!strcmp(argv[argi], "-h")) {
      usage(argv[0], 0);
    } else if (!strcmp(argv[argi], "--help")) {
      usage(argv[0], 0);

    } else if (!strcmp(argv[argi], "--info")) {
      showDecoderInfo();
      exit(0);

    } else if (
        !strcmp(argv[argi], "-i") || !strcmp(argv[argi], "--files-on-stdin")) {
      files_on_stdin = true;
      continue;

    } else if (!strcmp(argv[argi], "-d") || !strcmp(argv[argi], "--details")) {
      do_detailed_output = true;
      continue;

    } else if (!strcmp(argv[argi], "--pdq")) {
      do_pdqhash = true;
      do_pdqdih = false;
      continue;

    } else if (!strcmp(argv[argi], "--pdqdih")) {
      do_pdqhash = false;
      do_pdqdih = true;
      do_pdqdih_across = false;
      continue;

    } else if (!strcmp(argv[argi], "--pdqdih-across")) {
      do_pdqhash = false;
      do_pdqdih = true;
      do_pdqdih_across = true;
      continue;

    } else if (!strcmp(argv[argi], "-k")) {
      keep_going_after_errors = true;
      continue;

    } else {
      usage(argv[0], 1);
    }
  }

  // Iterate over image-file names.  One file at a time, compute per-file hash
  // and hamming distance to previous. (E.g. for video frame-taps).
  int num_pdqhash = 0;
  Hash256 pdqhash_prev;
  bool had_error = false;
  if (files_on_stdin) {
    if (argi < argc) {
      usage(argv[0], 1);
    }
    char* filename = nullptr;
    size_t linelen = 0;

    while ((ssize_t)(linelen = getline(&filename, &linelen, stdin)) != -1) {
      if (filename == nullptr) { // for lint
        fprintf(
            stderr,
            "Internal coding error detected in file %s at line %d.\n",
            __FILE__,
            __LINE__);
        exit(1);
      }
      if (linelen > 0) {
        if (filename[linelen - 1] == '\n') {
          filename[linelen - 1] = 0;
          linelen--;
        }
      }
      num_pdqhash++;
      process_file(
          argv[0],
          filename,
          do_pdqhash,
          do_pdqdih,
          do_pdqdih_across,
          do_detailed_output,
          keep_going_after_errors,
          num_pdqhash,
          pdqhash_prev,
          had_error);
      fflush(stdout);
    }
  } else {
    if (argi >= argc) {
      usage(argv[0], 1);
    }
    for (; argi < argc; argi++) {
      char* filename = argv[argi];
      num_pdqhash++;
      process_file(
          argv[0],
          filename,
          do_pdqhash,
          do_pdqdih,
          do_pdqdih_across,
          do_detailed_output,
          keep_going_after_errors,
          num_pdqhash,
          pdqhash_prev,
          had_error);
      fflush(stdout);
    }
  }

  return had_error ? 1 : 0;
}

// ----------------------------------------------------------------
void process_file(
    char* argv0,
    char* filename,
    bool do_pdqhash,
    bool do_pdqdih,
    bool do_pdqdih_across,
    bool do_detailed_output,
    bool keep_going_after_errors,
    int num_pdqhash,
    Hash256& pdqhash_prev,
    bool& had_error) {
  Hash256 pdqhash;
  Hash256 pdqhashRotate90;
  Hash256 pdqhashRotate180;
  Hash256 pdqhashRotate270;
  Hash256 pdqhashFlipX;
  Hash256 pdqhashFlipY;
  Hash256 pdqhashFlipPlus1;
  Hash256 pdqhashFlipMinus1;
  int norm;
  int delta;
  int quality;

  int imageHeightTimesWidthUnused = 0;
  float readSecondsUnused = 0.0;
  float hashSecondsUnused = 0.0;
  if (do_pdqhash) {
    try {
      facebook::pdq::hashing::pdqHash256FromFile(
        filename,
        pdqhash,
        quality,
        imageHeightTimesWidthUnused,
        readSecondsUnused,
        hashSecondsUnused
      );
    } catch (std::runtime_error& e) {
      fprintf(stderr, "%s: could not decode \"%s\".\n", argv0, filename);
      if (keep_going_after_errors) {
        had_error = true;
        return;
      } else {
        exit(1);
      }
    }
    norm = pdqhash.hammingNorm();
    delta = (num_pdqhash == 1) ? 0 : pdqhash.hammingDistance(pdqhash_prev);

    if (!do_detailed_output) {
      printf("%s,%d,%s\n", pdqhash.format().c_str(), quality, filename);
    } else {
      printf("hash=%s", pdqhash.format().c_str());
      printf(",norm=%d", norm);
      printf(",delta=%d", delta);
      printf(",quality=%d", quality);
      printf(",filename=%s\n", filename);
    }

    pdqhash_prev = pdqhash;
  }

  if (do_pdqdih) {
    try {
      (void)facebook::pdq::hashing::pdqDihedralHash256esFromFile(
          filename,
          &pdqhash,
          &pdqhashRotate90,
          &pdqhashRotate180,
          &pdqhashRotate270,
          &pdqhashFlipX,
          &pdqhashFlipY,
          &pdqhashFlipPlus1,
          &pdqhashFlipMinus1,
          quality,
          imageHeightTimesWidthUnused,
          readSecondsUnused,
          hashSecondsUnused);
    } catch (std::runtime_error& e) {
      fprintf(stderr, "%s: could not decode \"%s\".\n", argv0, filename);
      if (keep_going_after_errors) {
        had_error = true;
        return;
      } else {
        exit(1);
      }
    }

    if (!do_detailed_output) {
      if (do_pdqdih_across) {
        printf(
            "%s,%s,%s,%s,%s,%s,%s,%s,%d,%s\n",
            pdqhash.format().c_str(),
            pdqhashRotate90.format().c_str(),
            pdqhashRotate180.format().c_str(),
            pdqhashRotate270.format().c_str(),
            pdqhashFlipX.format().c_str(),
            pdqhashFlipY.format().c_str(),
            pdqhashFlipPlus1.format().c_str(),
            pdqhashFlipMinus1.format().c_str(),
            quality,
            filename);
      } else {
        printf("%s,%d,%s\n", pdqhash.format().c_str(), quality, filename);
        printf(
            "%s,%d,%s\n", pdqhashRotate90.format().c_str(), quality, filename);
        printf(
            "%s,%d,%s\n", pdqhashRotate180.format().c_str(), quality, filename);
        printf(
            "%s,%d,%s\n", pdqhashRotate270.format().c_str(), quality, filename);
        printf("%s,%d,%s\n", pdqhashFlipX.format().c_str(), quality, filename);
        printf("%s,%d,%s\n", pdqhashFlipY.format().c_str(), quality, filename);
        printf(
            "%s,%d,%s\n", pdqhashFlipPlus1.format().c_str(), quality, filename);
        printf(
            "%s,%d,%s\n",
            pdqhashFlipMinus1.format().c_str(),
            quality,
            filename);
      }

    } else {
      if (do_pdqdih_across) {
        printf("hash=%s", pdqhash.format().c_str());
        printf(",quality=%d", quality);

        printf(",orig=%s", pdqhash.format().c_str());
        printf(",rot90=%s", pdqhashRotate90.format().c_str());
        printf(",rot180=%s", pdqhashRotate180.format().c_str());
        printf(",rot270=%s", pdqhashRotate270.format().c_str());
        printf(",flipx=%s", pdqhashFlipX.format().c_str());
        printf(",flipy=%s", pdqhashFlipY.format().c_str());
        printf(",flipp=%s", pdqhashFlipPlus1.format().c_str());
        printf(",flipm=%s", pdqhashFlipMinus1.format().c_str());
        printf(",filename=%s\n", filename);

      } else {
        printf("hash=%s", pdqhash.format().c_str());
        printf(",quality=%d", quality);
        printf(",filename=%s\n", filename);

        printf(
            "hash=%s,xform=orig,filename=%s\n",
            pdqhash.format().c_str(),
            filename);
        printf(
            "hash=%s,xform=rot90,filename=%s\n",
            pdqhashRotate90.format().c_str(),
            filename);
        printf(
            "hash=%s,xform=rot180,filename=%s\n",
            pdqhashRotate180.format().c_str(),
            filename);
        printf(
            "hash=%s,xform=rot270,filename=%s\n",
            pdqhashRotate270.format().c_str(),
            filename);
        printf(
            "hash=%s,xform=flipx,filename=%s\n",
            pdqhashFlipX.format().c_str(),
            filename);
        printf(
            "hash=%s,xform=flipy,filename=%s\n",
            pdqhashFlipY.format().c_str(),
            filename);
        printf(
            "hash=%s,xform=flipp,filename=%s\n",
            pdqhashFlipPlus1.format().c_str(),
            filename);
        printf(
            "hash=%s,xform=flipm,filename=%s\n",
            pdqhashFlipMinus1.format().c_str(),
            filename);
      }
    }

    pdqhash_prev = pdqhash;
  }
}
