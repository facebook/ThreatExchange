// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

#include <pdq/cpp/common/pdqbasetypes.h>
#include <pdq/cpp/common/pdqhamming.h>

#include <pdq/cpp/io/pdqio.h>
#include <pdq/cpp/hashing/pdqhashing.h>
#include <pdq/cpp/hashing/torben.h>
#include <pdq/cpp/downscaling/downscaling.h>

#include <stdlib.h>
#include <stdio.h>
#include <string>

using namespace std;
using namespace cimg_library;
using namespace facebook::pdq::hashing;
using namespace facebook::pdq::downscaling;

static void floatMatrixToCImgOrDump(
  float* matrix, // matrix as num_rows x num_cols in row-major order
  int numRows,
  int numCols,
  char* filename,
  char fprintf_format[],
  bool do_dump
);

// ----------------------------------------------------------------
static void usage(char* argv0, int rc) {
  FILE* fp = (rc == 0) ? stdout : stderr;
  fprintf(fp, "Usage: %s [options] {one or more image-file names}\n", argv0);
  fprintf(fp, "Options:\n");
  fprintf(fp, "-h|--help: Print this message.\n");
  fprintf(fp,
    "--dump: Print numbers to stdout rather than writing tap files.\n");
  exit(rc);
}

// ----------------------------------------------------------------
// Demonstrates PDQ downscaling, primarily for documentation purposes.
// All the steps of pdq-photo-hasher but with tap-out files at each step.

int main(int argc, char* argv[]) {
  bool do_dump = false;
  int argi = 1;

  // Parse command-line flags. I'm explicitly not using gflags or other such
  // libraries, to minimize the number of external dependencies for this
  // project.
  for ( ; argi < argc; argi++) {
    if (argv[argi][0] != '-') {
      break;
    } else if (!strcmp(argv[argi], "-h")) {
      usage(argv[0], 0);
    } else if (!strcmp(argv[argi], "--help")) {
      usage(argv[0], 0);
    } else if (!strcmp(argv[argi], "--dump")) {
      do_dump = true;
    } else {
      usage(argv[0], 1);
    }
  }

  if (argi >= argc) {
    fprintf(stderr, "%s: need at least one image-file name.\n", argv[0]);
    usage(argv[0], 1);
  }

  char ffmt[] = "%11.7f";
  char gfmt[] = "%5.0f";

  for ( ; argi < argc; argi++) {
    char* filename = argv[argi];
    int tapbuflen = strlen(filename) + 32;
    char* tapName = new char[tapbuflen];

    CImg<uint8_t> src;
    try {
      src.load(filename);
    } catch (const CImgIOException& ex){
      fprintf(stderr, "%s: could not read image file \"%s\".\n",
        argv[0], filename);
      exit(1);
    }

    int numRows, numCols;
    float* buffer1 = loadFloatLumaFromCImg(src, numRows, numCols);
    float* buffer2 = new float[numRows * numCols];
    float buffer64x64[64][64];
    float buffer16x64[16][64];
    float buffer16x16[16][16];
    float buffer16x16Aux[16][16];

    snprintf(tapName, tapbuflen, "1-luma-%s", filename);
    floatMatrixToCImgOrDump(buffer1, numRows, numCols, tapName, ffmt, do_dump);

    int windowSizeAlongRows = computeJaroszFilterWindowSize(numCols, 64);
    int windowSizeAlongCols = computeJaroszFilterWindowSize(numRows, 64);

    facebook::pdq::downscaling::boxAlongRowsFloat(buffer1, buffer2, numRows, numCols, windowSizeAlongRows);
    snprintf(tapName, tapbuflen, "2-x1-%s", filename);
    floatMatrixToCImgOrDump(buffer2, numRows, numCols, tapName, ffmt, do_dump);

    facebook::pdq::downscaling::boxAlongColsFloat(buffer2, buffer1, numRows, numCols, windowSizeAlongCols);
    snprintf(tapName, tapbuflen, "3-y1-%s", filename);
    floatMatrixToCImgOrDump(buffer1, numRows, numCols, tapName, ffmt, do_dump);

    facebook::pdq::downscaling::decimateFloat(buffer1, numRows, numCols, &buffer64x64[0][0], 64, 64);
    snprintf(tapName, tapbuflen, "4-ds-%s", filename);
    floatMatrixToCImgOrDump(&buffer64x64[0][0], 64, 64, tapName, ffmt, do_dump);

    facebook::pdq::downscaling::boxAlongRowsFloat(buffer1, buffer2, numRows, numCols, windowSizeAlongRows);
    snprintf(tapName, tapbuflen, "4-x2-%s", filename);
    floatMatrixToCImgOrDump(buffer2, numRows, numCols, tapName, ffmt, do_dump);

    facebook::pdq::downscaling::boxAlongColsFloat(buffer2, buffer1, numRows, numCols, windowSizeAlongCols);
    snprintf(tapName, tapbuflen, "5-y2-%s", filename);
    floatMatrixToCImgOrDump(buffer1, numRows, numCols, tapName, ffmt, do_dump);

    facebook::pdq::downscaling::decimateFloat(buffer1, numRows, numCols, &buffer64x64[0][0], 64, 64);
    snprintf(tapName, tapbuflen, "6-ds-%s", filename);
    floatMatrixToCImgOrDump(&buffer64x64[0][0], 64, 64, tapName, ffmt, do_dump);


    dct64To16(buffer64x64, buffer16x64, buffer16x16);
    snprintf(tapName, tapbuflen, "7-dct-%s", filename);
    floatMatrixToCImgOrDump(&buffer16x16[0][0], 16, 16, tapName, gfmt, do_dump);

    if (do_dump) {
      float dct_median = torben(&buffer16x16[0][0], 16 * 16);
      printf("Median: %.4f\n", dct_median);
      printf("\n");
    }

    dct16OriginalToRotate90(buffer16x16, buffer16x16Aux);
    snprintf(tapName, tapbuflen, "7-dct-r90-%s", filename);
    floatMatrixToCImgOrDump(&buffer16x16Aux[0][0], 16, 16, tapName, gfmt, do_dump);

    dct16OriginalToRotate180(buffer16x16, buffer16x16Aux);
    snprintf(tapName, tapbuflen, "7-dct-r180-%s", filename);
    floatMatrixToCImgOrDump(&buffer16x16Aux[0][0], 16, 16, tapName, gfmt, do_dump);

    dct16OriginalToRotate270(buffer16x16, buffer16x16Aux);
    snprintf(tapName, tapbuflen, "7-dct-r270-%s", filename);
    floatMatrixToCImgOrDump(&buffer16x16Aux[0][0], 16, 16, tapName, gfmt, do_dump);

    dct16OriginalToFlipX(buffer16x16, buffer16x16Aux);
    snprintf(tapName, tapbuflen, "7-dct-fx-%s", filename);
    floatMatrixToCImgOrDump(&buffer16x16Aux[0][0], 16, 16, tapName, gfmt, do_dump);

    dct16OriginalToFlipY(buffer16x16, buffer16x16Aux);
    snprintf(tapName, tapbuflen, "7-dct-fy-%s", filename);
    floatMatrixToCImgOrDump(&buffer16x16Aux[0][0], 16, 16, tapName, gfmt, do_dump);

    dct16OriginalToFlipPlus1(buffer16x16, buffer16x16Aux);
    snprintf(tapName, tapbuflen, "7-dct-fp-%s", filename);
    floatMatrixToCImgOrDump(&buffer16x16Aux[0][0], 16, 16, tapName, gfmt, do_dump);

    dct16OriginalToFlipMinus1(buffer16x16, buffer16x16Aux);
    snprintf(tapName, tapbuflen, "7-dct-fm-%s", filename);
    floatMatrixToCImgOrDump(&buffer16x16Aux[0][0], 16, 16, tapName, gfmt, do_dump);

    delete[] buffer1;
    delete[] buffer2;
  }

  return 0;
}

// ----------------------------------------------------------------
static void floatMatrixToCImgOrDump(
  float* matrix,
  int numRows,
  int numCols,
  char* filename,
  char fprintf_format[],
  bool do_dump
) {
  if (do_dump) {
    int maxdim = 64;

    printf("%s:\n", filename);

   int nrcap = numRows;
   if (nrcap > maxdim)
     nrcap = maxdim;

   int nccap = numCols;
   if (nccap > maxdim)
     nccap = maxdim;

   for (int i = 0; i < nrcap; i++) {
     for (int j = 0; j < nccap; j++) {
       printf(fprintf_format, matrix[i * numCols + j]);
       if (j < (nccap - 1)) {
         printf(" ");
       } else {
         printf("\n");
       }
     }
   }
    printf("\n");
  } else {
    CImg<float> cimg(numCols, numRows);
    for (int i = 0; i < numRows; i++) {
      for (int j = 0; j < numCols; j++) {
        cimg(j, i) = matrix[i * numCols + j];
      }
    }
    cimg.save(filename);
  }
}
