// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

// ================================================================
// Basic allocation and math routines for operating on vectors. Nothing
// original, but I don't want to introduce additional third-party package
// dependencies. These routines keep things simple and local.
//
// Note that one of the primary reasons we are developing TMK is for
// data-sharing with other companies. So I want as few dependencies
// as possible.
// ================================================================

#include <tmk/cpp/lib/vec.h>
#include <stdio.h>
#include <cmath>

namespace facebook {
namespace tmk {
namespace libvec {

// ----------------------------------------------------------------
float computeMax(const std::vector<float>& u) {
  int n = u.size();
  if (n < 1) {
    return 0.0;
  }
  float vmax = u[0];
  for (int i = 1; i < n; i++) {
    float e = u[i];
    if (vmax < e) {
      vmax = e;
    }
  }
  return vmax;
}

// ----------------------------------------------------------------
float computeSum(const std::vector<float>& u) {
  int n = u.size();
  float sum = 0.0;
  for (int i = 0; i < n; i++) {
    sum += u[i];
  }
  return sum;
}

// ----------------------------------------------------------------
float computeNorm(const std::vector<float>& u) {
  float sum = 0.0;
  int n = u.size();
  for (int i = 0; i < n; i++) {
    float e = u[i];
    sum += e * e;
  }
  return std::sqrt(sum);
}

// ----------------------------------------------------------------
// Euclidan distance (and distance-squared) have the property that they are
// the sums of non-negative terms. So if we want to check if d^2(u,v) <= t,
// we can break out of the loop as soon as the partial sum is >= t. This is
// a performance improvement (depending on the distibution of u and v).
bool distanceSquaredLE(
    const std::vector<float>& u,
    const std::vector<float>& v,
    float threshold,
    float& dsq // If return value is true, this is the full distance squared.
) {
  dsq = 0.0;
  int n = u.size();
  for (int i = 0; i < n; i++) {
    float diff = u[i] - v[i];
    dsq += diff * diff;
    if (dsq > threshold) {
      return false;
    }
  }
  return true;
}

// ----------------------------------------------------------------
float computeDistance(
    const std::vector<float>& u,
    const std::vector<float>& v
) {
  float dsq = 0.0;
  int n = u.size();
  for (int i = 0; i < n; i++) {
    float diff = u[i] - v[i];
    dsq += diff * diff;
  }
  return std::sqrt(dsq);
}

// ----------------------------------------------------------------
float computeDot(const std::vector<float>& u, const std::vector<float>& v) {
  float sum = 0.0;
  int n = u.size();
  for (int i = 0; i < n; i++) {
    sum += u[i] * v[i];
  }
  return sum;
}

// ----------------------------------------------------------------
float computeCosSim(const std::vector<float>& u, const std::vector<float>& v) {
  float nu = computeNorm(u);
  float nv = computeNorm(v);
  if (nu == 0.0 && nv == 0.0) {
    return 0.0;
  } else {
    return computeDot(u, v) / (computeNorm(u) * computeNorm(v));
  }
}

// ----------------------------------------------------------------
void scalarMultiply(std::vector<float>& u, float s) {
  int n = u.size();
  for (int i = 0; i < n; i++) {
    u[i] *= s;
  }
}

// ----------------------------------------------------------------
void scalarDivide(std::vector<float>& u, float s) {
  int n = u.size();
  for (int i = 0; i < n; i++) {
    u[i] /= s;
  }
}

// ----------------------------------------------------------------
void L2NormalizeVector(std::vector<float>& v) {
  float norm = computeNorm(v);
  if (norm > 0.0) {
    scalarDivide(v, norm);
  }
}

// ----------------------------------------------------------------
std::vector<std::vector<float>> allocateRank2(int length1, int length2) {
  std::vector<std::vector<float>> retval =
      std::vector<std::vector<float>>(length1);
  for (int i = 0; i < length1; i++) {
    retval[i] = std::vector<float>(length2);
    for (int j = 0; j < length2; j++) {
      retval[i][j] = 0.0;
    }
  }
  return retval;
}

// ----------------------------------------------------------------
std::vector<std::vector<std::vector<float>>>
allocateRank3(int length1, int length2, int length3) {
  std::vector<std::vector<std::vector<float>>> retval =
      std::vector<std::vector<std::vector<float>>>(length1);
  for (int i = 0; i < length1; i++) {
    retval[i] = std::vector<std::vector<float>>(length2);
    for (int j = 0; j < length2; j++) {
      retval[i][j] = std::vector<float>(length3);
      for (int k = 0; k < length3; k++) {
        retval[i][j][k] = 0.0;
      }
    }
  }
  return retval;
}

// ----------------------------------------------------------------
bool checkDimensionsRank3(
    const std::vector<std::vector<std::vector<float>>>& u,
    int length1,
    int length2,
    int length3) {
  if (u.size() != length1) {
    return false;
  }
  for (int i = 0; i < u.size(); i++) {
    if (u[i].size() != length2) {
      return false;
    }
    for (int j = 0; j < u[i].size(); j++) {
      if (u[i][j].size() != length3) {
        return false;
      }
    }
  }
  return true;
}

bool compareFloats(float a, float b, float tolerance) {
  float m = std::fmax(std::fabs(a), std::fabs(b));
  if (m > 0) {
    float relerr = std::fabs((a - b) / m);
    if (relerr > tolerance) {
      return false;
    }
    return true;
  }
  return true; // both are true
}

bool compareVectors(
    const std::vector<float>& u,
    const std::vector<float>& v,
    float tolerance) {
  if (u.size() != v.size()) {
    printf("SIZE OUT\n");
    return false;
  }
  for (int i = 0; i < u.size(); i++) {
    if (!(compareFloats(u[i], v[i], tolerance))) {
    printf("I OUT %d %.4f %.4f\n", i, u[i], v[i]);
      return false;
    }
  }
  printf("OK\n");
  return true;
}

bool compareVectorsRank3(
    const std::vector<std::vector<std::vector<float>>>& u,
    const std::vector<std::vector<std::vector<float>>>& v,
    float tolerance) {
  if (!(checkDimensionsRank3(u, v.size(), v[0].size(), v[0][0].size()))) {
    return false;
  }
  for (int i = 0; i < u.size(); i++) {
    for (int j = 0; j < u[i].size(); j++) {
      if (!(compareVectors(u[i][j], v[i][j], tolerance))) {
        return false;
      }
    }
  }
  return true;
}

} // namespace libvec
} // namespace tmk
} // namespace facebook
