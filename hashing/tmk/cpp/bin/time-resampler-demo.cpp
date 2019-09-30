// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

// ================================================================
// This is intended to operate the time-resampler in isolation from actual
// `.mp4` files -- for regression, as well as for code clarity.
// ================================================================

// g++ -std=c++11 timeresamplers.cpp time-resampler-demo.cpp
// a.out 5 5 4
// a.out 5 8 4
// a.out 8 5 4

#include <stdio.h>
#include <stdlib.h>
#include <tmk/cpp/raster/timeresamplers.h>

using namespace facebook::tmk;
using namespace facebook::tmk::raster;

// ================================================================
int main(int argc, char** argv) {
  double ifps = 20.0;
  int ofps = 8;
  double inputLength = 0.0;

  if (argc != 4) {
    fprintf(
        stderr, "Usage: %s {ifps} {ofps} {input length in seconds}\n", argv[0]);
    exit(1);
  }
  (void)sscanf(argv[1], "%lf", &ifps);
  (void)sscanf(argv[2], "%d", &ofps);
  (void)sscanf(argv[3], "%lf", &inputLength);

  auto ptimeResampler = TimeResamplerFactory::createTimeResampler(ifps, ofps);

  int ofno = 0.0;
  for (int ifno = 0;; ifno++) {
    double istamp = ptimeResampler->inputFrameNumberToTimestamp(ifno);
    if (istamp >= inputLength) {
      break;
    }
    int oct = ptimeResampler->numberToEmit();
    if (oct == 0) {
      printf("ifno %4d istamp %11.6lf\n", ifno, istamp);
    }
    for (int j = 0; j < oct; j++) {
      double ostamp = ptimeResampler->outputFrameNumberToTimestamp(ofno);
      printf(
          "ifno %4d istamp %11.6lf ofno %4d ostamp %11.6lf  repct %2d\n",
          ifno,
          istamp,
          ofno,
          ostamp,
          j);
      ofno++;
    }
  }
  return 0;
}
