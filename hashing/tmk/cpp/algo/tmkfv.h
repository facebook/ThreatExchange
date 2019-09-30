// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

// ================================================================
// Wrapper class for TMK feature-vectors. It includes methods for
// computing them on a streaming basis from frame-features, one frame-feature
// at a time, as well as methods for manipulating them when loaded from disk.
// ================================================================

// ================================================================
// TMK NORMALIZED SCORING:
//
// The level-1 score is the cosine similarity between two pure-average
// features.  It is not TMK.  It is a criterion we use to determine whether or
// not to compute the full TMK pair score. (It has been found that when the
// level-1 scores differ significantly, the level-2 scores will as well, so the
// expensive level-2 score can be skipped. On the other hand, if the level-1
// scores are close, the level-2 scores might not be.)
//
// The TMK pair score (a.k.a. level-2 score) is as follows:
//
// For single videos:
// * Have P periods (nominally four of them).
// * Have m fourier coefficents a_0 through a_{m-1} (nominally m=32).
// * Note that the dot product is bilinear on vectors u and v so if u and v
//   are both scaled by sqrt(a_j) then their dot is scaled by a_j.
// * For each period accumulate m cosine features and m sine features.
// * Suppose there are N frame-features ("frame hashes").
// * L2-normalize these.
// * 0th cosine feature is sqrt(a_0) sum_{over frames} (frame feature)
// * 0th sine feature is always zero
// * jth cosine feature is sqrt(a_j) sum_{over frames} (frame feature
//     times cos(2 pi j t T))
//   where T is the period and t is the integer timestamp of the frame
// * jth sine feature is sqrt(a_j) sum_{over frames} (frame feature
//     times sin(2 pi j t T))
//   where T is the period and t is the integer timestamp of the frame
// * Once frame-features are all ingested then L2-normalize all the
//   cosine/sine features and then scale by sqrt(a_j).
//
// To score a pair of videos:
// * For each period T iterate over all offsets 0 .. T-1
// * For a given period and offset compute (see Poullot or Baraldi paper)
//   o delta = 2 pi offset / period
//   o Let u_{c,j} and u_{s,j} be the jth cosine/sine feature for the 1st video
//   o Let v_{c,j} and v_{s,j} be the jth cosine/sine feature for the 1st video
//   o Recall these have norm a_j: each vector is scaled by sqrt(a_j) so norms
//     are a_j.
//   o K_delta = u_{c,0} . v_{c,0}
//     + sum_{j=1}^{m-1} cos(j delta) * (u_{c,j} . v_{c,j} + u_{s,j} . v_{s,j})
//     + sum_{j=1}^{m-1} sin(j delta) * (u_{s,j} . v_{c,j} - u_{c,j} . v_{s,j})
// * For a given period, the TMK score is the maximum of K_delta for all
//   offsets.
// * The TMK score for the pair of videos is either the max or sum over all
//   periods.
//
// All well and good but now we need to normalize these to get a score between
// 0 and 1.
//
// To get that, suppose we are scoring a video with itself. This means each
// feature u_{.,j} == v_{.,j} and best offset is delta = 0.
//
// Then for each period,
//
//   K_delta = u_{c,0} . u_{c,0}
//   + sum_{j=1}^{m-1} cos(j delta) * (u_{c,j} . u_{c,j} + u_{s,j} . u_{s,j})
//   + sum_{j=1}^{m-1} sin(j delta) * (u_{s,j} . u_{c,j} - u_{c,j} . u_{s,j})
//
// Since u_{.,j} . u_{.,j} = a_j (normalization) this is
//
//   K_delta = a_0
//   + sum_{j=1}^{m-1} cos(j delta) * 2 a_j
//   + sum_{j=1}^{m-1} sin(j delta) * 0
//
//   = a_0 + 2 sum_{j=1}^{m-1} cos(j delta)
//
// and since delta = 0 at best offset for self-scoring
//
//   K_0 = a_0 + 2 sum_{j=1}^{m-1} a_j
//
// In the code below, this sum
//
//   a_0 + 2 sum_{j=1}^{m-1} a_j
//
// is called _pairScoreNormalizer.
// ================================================================

#ifndef TMKFV_H
#define TMKFV_H

#include <stdio.h>
#include <tmk/cpp/io/tmkio.h>
#include <memory>
#include <vector>

namespace facebook {
namespace tmk {
namespace algo {

// ----------------------------------------------------------------
// TMK ingests frame-features or hashes. They are accumulated as time-weighted
// sums index by fourier period, then by fourier coefficients.

// These are parameters for TMK frame-feature processing:
using Periods = std::vector<int>;
// These are parameters for TMK frame-feature processing:
using FourierCoefficients = std::vector<float>;
// These are input to TMK frame-feature processing, also used for TMK
// internal state:
using FrameFeature = std::vector<float>;

// TMK internal state: The cosine/sine-feature dimensions are
//
// (numPeriods x numFourierCoefficients x frameFeatureDimension).
//
// If either numPeriods or numFourierCoefficients (or both) is zero then
// only the pure-average "level-1" feature will be computed.
using FeaturesByFourierCoefficient = std::vector<FrameFeature>;
using FeaturesByPeriodsAndFourierCoefficients =
    std::vector<FeaturesByFourierCoefficient>;

// TMK alignment. Length is number of periods. These are used for detailed
// TMK-alignment values (when desired).
using BestOffsets = std::vector<int>;
using ValuesAtBestOffsets = std::vector<float>;

const int TMK_DEFAULT_RESAMPLE_FPS = 15;

// ================================================================
class TMKFeatureVectors {
  // ----------------------------------------------------------------
 private:
  facebook::tmk::io::TMKFramewiseAlgorithm _algorithm;

  int _framesPerSecond; // provenance of the data

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // Input coefficients
  Periods _periods;

  FourierCoefficients _fourierCoefficients;

  int _frameFeatureDimension;
  int _frameFeatureCount;

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // Output features

  // This is guaranteed to be independent of any model-training parameters.
  FrameFeature _pureAverageFeature;

  // These ones may depend on model-training parameters.

  // As noted above, the cosine/sine-feature dimensions are
  //
  //   (numPeriods x numFourierCoefficients x frameFeatureDimension).
  //
  // This means:
  // * Outer index is 0 to _periods.size() - 1 inclusive.
  // * Middle index is 0 to _fourierCoefficients.size() - 1 inclusive.
  // * Inner index is 0 to _frameFeatureDimension - 1 inclusive.
  //
  // This therefore means that cosine/sine-feature dimensions
  // are (numPeriods x numFourierCoefficients x frameFeatureDimension).
  FeaturesByPeriodsAndFourierCoefficients _cosFeatures;
  FeaturesByPeriodsAndFourierCoefficients _sinFeatures;

  // When we compute the TMK score of a hashed video with itself, we want 1.0.
  // This number does that. The algebraic derivation is above.
  float _pairScoreNormalizer;

  // ----------------------------------------------------------------
 public:
  TMKFeatureVectors() {}

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // For constructing before computing from frame features.
  TMKFeatureVectors(
      facebook::tmk::io::TMKFramewiseAlgorithm algorithm, // provenance
      int framesPerSecond, // provenance
      const Periods& periods,
      const FourierCoefficients& fourierCoefficients,
      int frameFeatureDimension);

  // For constructing after computing from frame features, e.g.  load from
  // file. Since it is possible for the dimensions to be inconsistent, we make
  // this private and provide access via a factory method.
 private:
  TMKFeatureVectors(
      facebook::tmk::io::TMKFramewiseAlgorithm algorithm, // provenance
      int framesPerSecond, // provenance
      int frameFeatureCount, // informational
      const Periods& periods,
      const FourierCoefficients& fourierCoefficients,
      const FrameFeature& pureAverageFeature,
      const FeaturesByPeriodsAndFourierCoefficients& cosFeatures,
      const FeaturesByPeriodsAndFourierCoefficients& sinFeatures);

 public:
  // See the above private constructor. This is used for reading precomputed
  // results from storage.
  static std::shared_ptr<TMKFeatureVectors> tryCreateFromPrecomputed(
      facebook::tmk::io::TMKFramewiseAlgorithm algorithm,
      int framesPerSecond,
      int frameFeatureCount,
      const Periods& periods,
      const FourierCoefficients& fourierCoefficients,
      const FrameFeature& pureAverageFeature,
      const FeaturesByPeriodsAndFourierCoefficients& cosFeatures,
      const FeaturesByPeriodsAndFourierCoefficients& sinFeatures);

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // Checks the two are computed using the same periods, same framewise hasher,
  // etc.
  static bool areCompatible(
      const TMKFeatureVectors& fva,
      const TMKFeatureVectors& fvb);

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  static Periods makePoullotPeriods();
  static FourierCoefficients makePoullotFourierCoefficients();

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  void ingestFrameFeature(const FrameFeature& frameFeature, int frameNumber);

  void finishFrameFeatureIngest();

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  bool writeToOutputStream(FILE* fp, const char* programName) const;

  bool writeToOutputFile(const char* fileName, const char* programName) const;

  static std::shared_ptr<TMKFeatureVectors> readFromInputStream(
      FILE* fp,
      const char* programName);
  static std::shared_ptr<TMKFeatureVectors> readFromInputFile(
      const char* fileName,
      const char* programName);

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  facebook::tmk::io::TMKFramewiseAlgorithm getAlgorithm() const {
    return _algorithm;
  }

  int getNumPeriods() const {
    return _periods.size();
  }
  int getNumFourierCoefficients() const {
    return _fourierCoefficients.size();
  }
  int getFrameFeatureDimension() const {
    return _frameFeatureDimension;
  }

  int getFramesPerSecond() const {
    return _framesPerSecond;
  }

  int getFrameFeatureCount() const {
    return _frameFeatureCount;
  }

  Periods getPeriods() const {
    return _periods;
  }

  FourierCoefficients getFourierCoefficients() const {
    return _fourierCoefficients;
  }

  FrameFeature getPureAverageFeature() const {
    return _pureAverageFeature;
  }

  FeaturesByPeriodsAndFourierCoefficients getCosFeatures() const {
    return _cosFeatures;
  }

  FeaturesByPeriodsAndFourierCoefficients getSinFeatures() const {
    return _sinFeatures;
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  void L2NormalizePureAverageFeature();

  static void findPairOffsetsModuloPeriods(
      const TMKFeatureVectors& fva,
      const TMKFeatureVectors& fvb,
      BestOffsets& bestOffsets,
      ValuesAtBestOffsets& valuesAtBestOffsets,
      bool printDetails);

  static float computeLevel1Score(
      const TMKFeatureVectors& fva,
      const TMKFeatureVectors& fvb);

  static float computeLevel2Score(
      const TMKFeatureVectors& fva,
      const TMKFeatureVectors& fvb);

  static bool compare(
      const TMKFeatureVectors& fva,
      const TMKFeatureVectors& fvb,
      float tolerance);
};

} // namespace algo
} // namespace tmk
} // namespace facebook

#endif // TMKFV_H
