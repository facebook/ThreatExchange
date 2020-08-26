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

#ifndef TMKVECLIB_H
#define TMKVECLIB_H

#include <vector>

namespace facebook {
namespace tmk {
namespace libvec {

float computeMax(const std::vector<float>& u);

float computeSum(const std::vector<float>& u);

float computeNorm(const std::vector<float>& u);

bool distanceSquaredLE(
    const std::vector<float>& u,
    const std::vector<float>& v,
    float threshold,
    float& dsq // Contains full distance-squared if return value is true.
);

float computeDistance(
    const std::vector<float>& u,
    const std::vector<float>& v
);

float computeDot(const std::vector<float>& u, const std::vector<float>& v);

float computeCosSim(const std::vector<float>& u, const std::vector<float>& v);

void scalarMultiply(std::vector<float>& u, float s);
void scalarDivide(std::vector<float>& u, float s);

void L2NormalizeVector(std::vector<float>& v);

std::vector<std::vector<float>> allocateRank2(int length1, int length2);

std::vector<std::vector<std::vector<float>>>
allocateRank3(int length1, int length2, int length3);

bool checkDimensionsRank3(
    const std::vector<std::vector<std::vector<float>>>& u,
    int length1,
    int length2,
    int length3);

bool compareFloats(float a, float b, float tolerance);

bool compareVectors(
    const std::vector<float>& u,
    const std::vector<float>& v,
    float tolerance);

bool compareVectorsRank3(
    const std::vector<std::vector<std::vector<float>>>& u,
    const std::vector<std::vector<std::vector<float>>>& v,
    float tolerance);

} // namespace libvec
} // namespace tmk
} // namespace facebook

#endif // TMKVECLIB_H
