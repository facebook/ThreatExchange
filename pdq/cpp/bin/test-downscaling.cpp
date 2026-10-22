// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#include <pdq/cpp/downscaling/downscaling.h>

#include <climits>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <vector>

// ================================================================
// Regression tests for pdq/cpp/downscaling/downscaling.cpp, added for
// facebook/ThreatExchange#1979 (signed-int overflow in box1DFloat /
// boxAlongRowsFloat / decimateFloat index arithmetic).
//
// Two things are checked:
//   (1) Behavior is preserved on normal/non-square inputs (the fix is a pure
//       type widening with no algorithmic change).
//   (2) The widened index arithmetic computes the correct, non-wrapping offset
//       at magnitudes where the previous `int * int` form was UB. These are
//       lightweight arithmetic checks -- they do NOT allocate multi-GB buffers.
// ================================================================

using namespace facebook::pdq::downscaling;

static int g_fails = 0;

#define CHECK(cond, msg)                                      \
  do {                                                        \
    if (!(cond)) {                                            \
      printf("FAIL: %s  (%s:%d)\n", msg, __FILE__, __LINE__); \
      g_fails++;                                              \
    }                                                         \
  } while (0)

#define CHECK_EQ_F(got, want, msg)                                           \
  do {                                                                       \
    if ((got) != (want)) {                                                   \
      printf(                                                                \
          "FAIL: %s  got=%g want=%g\n", msg, (double)(got), (double)(want)); \
      g_fails++;                                                             \
    }                                                                        \
  } while (0)

// ----------------------------------------------------------------
// box1DFloat averages over a sliding window; for a constant input every
// output element must equal that constant. Exactly `vector_length` elements
// are written, so this exercises every phase and the full index range.
static void test_box1DFloat_constant(
    int vector_length, int stride, int window) {
  int n = vector_length * stride;
  std::vector<float> in((size_t)n, 7.5f);
  std::vector<float> out((size_t)n, -1.0f);
  // Offset base pointers by (stride-1) to mimic the column path's &in[j].
  int base = stride - 1;
  box1DFloat(&in[base], &out[base], vector_length, stride, window);
  for (int k = 0; k < vector_length; k++) {
    CHECK_EQ_F(
        out[(size_t)base + (size_t)k * stride],
        7.5f,
        "box1DFloat constant-input should pass constant through");
  }
}

// ----------------------------------------------------------------
// decimateFloat is a deterministic nearest-neighbor pick of centers. Hand
// computed for a 4x4 -> 2x2 reduction of in[r*4+c] = r*4+c.
static void test_decimateFloat_known() {
  float in[16];
  for (int k = 0; k < 16; k++) {
    in[k] = (float)k;
  }
  float out[4] = {-1, -1, -1, -1};
  decimateFloat(in, 4, 4, out, 2, 2);
  // outi=0 -> ini=1 ; outi=1 -> ini=3 ; outj=0 -> inj=1 ; outj=1 -> inj=3
  CHECK_EQ_F(out[0], 5.0f, "decimate out[0,0] = in[1,1]");
  CHECK_EQ_F(out[1], 7.0f, "decimate out[0,1] = in[1,3]");
  CHECK_EQ_F(out[2], 13.0f, "decimate out[1,0] = in[3,1]");
  CHECK_EQ_F(out[3], 15.0f, "decimate out[1,1] = in[3,3]");
}

// ----------------------------------------------------------------
// Non-square decimate: 2x6 -> 2x3, values = r*6+c.
static void test_decimateFloat_nonsquare() {
  float in[12];
  for (int k = 0; k < 12; k++) {
    in[k] = (float)k;
  }
  float out[6] = {-1, -1, -1, -1, -1, -1};
  decimateFloat(in, 2, 6, out, 2, 3);
  // ini: outi0->0, outi1->1 ; inj: outj0->1, outj1->3, outj2->5
  CHECK_EQ_F(out[0], 1.0f, "nonsq out[0,0]");
  CHECK_EQ_F(out[1], 3.0f, "nonsq out[0,1]");
  CHECK_EQ_F(out[2], 5.0f, "nonsq out[0,2]");
  CHECK_EQ_F(out[3], 7.0f, "nonsq out[1,0]");
  CHECK_EQ_F(out[4], 9.0f, "nonsq out[1,1]");
  CHECK_EQ_F(out[5], 11.0f, "nonsq out[1,2]");
}

// ----------------------------------------------------------------
// fillFloatLumaFromGrey is a strided copy; luma[i*cols+j] must equal pixel.
static void test_fillFloatLumaFromGrey() {
  const int R = 3, C = 5;
  uint8_t img[R * C];
  for (int k = 0; k < R * C; k++) {
    img[k] = (uint8_t)(k * 3 + 1);
  }
  float luma[R * C];
  fillFloatLumaFromGrey(img, R, C, /*rowStride*/ C, /*colStride*/ 1, luma);
  for (int i = 0; i < R; i++) {
    for (int j = 0; j < C; j++) {
      CHECK_EQ_F(luma[i * C + j], (float)img[i * C + j], "luma copy");
    }
  }
}

// ----------------------------------------------------------------
// The fix: offsets are computed in size_t and stay correct past INT_MAX.
// These mirror the exact expression forms in downscaling.cpp without
// allocating anything. Performing the arithmetic in `int` (the old code)
// would be signed overflow (UB) at these magnitudes.
static void test_offset_boundary_arithmetic() {
  struct Case {
    int rowIdx; // e.g. (numRows-1) or ini
    int cols; // numCols / inNumCols
    int colIdx; // + j / + inj
    uint64_t want; // mathematically correct offset
  };
  // 99999*25000 = 2,499,975,000 ; +24999 = 2,499,999,999
  // 59999*60000 = 3,599,940,000
  Case cases[] = {
      {99999, 25000, 0, 2499975000ULL},
      {99999, 25000, 24999, 2499999999ULL},
      {59999, 60000, 0, 3599940000ULL},
  };
  for (const Case& c : cases) {
    size_t off = (size_t)c.rowIdx * c.cols + c.colIdx; // the patched form
    CHECK((uint64_t)off == c.want, "size_t offset matches true product");
    CHECK(
        (uint64_t)off > (uint64_t)INT_MAX,
        "offset exceeds INT_MAX (int form would have overflowed)");
    // Show, without signed-overflow UB, that a 32-bit signed result would be
    // wrong/negative -- i.e. the old code's index was corrupt here.
    uint32_t trunc32 =
        (uint32_t)c.rowIdx * (uint32_t)c.cols + (uint32_t)c.colIdx;
    int32_t as_signed = (int32_t)trunc32;
    CHECK(
        (uint64_t)as_signed != c.want,
        "32-bit signed interpretation differs from true offset");
    printf(
        "  offset(%d*%d+%d): size_t=%llu  int32-truncated=%d\n",
        c.rowIdx,
        c.cols,
        c.colIdx,
        (unsigned long long)off,
        as_signed);
  }
}

// ----------------------------------------------------------------
int main() {
  printf("================================================================\n");
  printf("downscaling.cpp regression tests (ThreatExchange#1979)\n\n");

  test_box1DFloat_constant(16, 1, 7); // row path
  test_box1DFloat_constant(16, 1, 8);
  test_box1DFloat_constant(10, 13, 5); // column path (stride=numCols)
  test_decimateFloat_known();
  test_decimateFloat_nonsquare();
  test_fillFloatLumaFromGrey();
  test_offset_boundary_arithmetic();

  printf(
      "\n%s (%d failure%s)\n",
      g_fails == 0 ? "ALL PASS" : "FAILURES",
      g_fails,
      g_fails == 1 ? "" : "s");
  printf("================================================================\n");
  return g_fails == 0 ? 0 : 1;
}
