// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

// ================================================================
// Wrapper class for TMK feature-vectors. It includes methods for
// computing them on a streaming basis from frame-features, one frame-feature
// at a time, as well as methods for manipulating them when loaded from disk.
// ================================================================

#include <tmk/cpp/algo/tmkfv.h>
#include <tmk/cpp/lib/vec.h>

#include <cmath>
#include <stdexcept>

namespace facebook {
namespace tmk {
namespace algo {

static const double pi = 3.14159265358979323846;

// ----------------------------------------------------------------
// See comments in tmkfv.h.
static float computePairScoreNormalizer(
    const FourierCoefficients& fourierCoefficients) {
  if (fourierCoefficients.size() == 0) {
    return 1.0;
  } else {
    float pairScoreNormalizer = fourierCoefficients[0];
    for (int j = 1; j < fourierCoefficients.size(); j++) {
      pairScoreNormalizer += 2.0 * fourierCoefficients[j];
    }
    return pairScoreNormalizer;
  }
}

// ----------------------------------------------------------------
// Constructor for beginning to compute TMK feature vectors from
// framewise hashes.
TMKFeatureVectors::TMKFeatureVectors(
    facebook::tmk::io::TMKFramewiseAlgorithm algorithm,
    int framesPerSecond,
    const Periods& periods,
    const FourierCoefficients& fourierCoefficients,
    int frameFeatureDimension)
    : _algorithm(algorithm),
      _framesPerSecond(framesPerSecond),
      _periods(periods),
      _fourierCoefficients(fourierCoefficients),
      _frameFeatureDimension(frameFeatureDimension),
      _frameFeatureCount(0) {
  int numPeriods = periods.size();
  int numFourierCoefficients = fourierCoefficients.size();

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  _pureAverageFeature = FrameFeature(frameFeatureDimension);
  for (int j = 0; j < frameFeatureDimension; j++) {
    _pureAverageFeature[j] = 0.0;
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  _cosFeatures = facebook::tmk::libvec::allocateRank3(
      numPeriods, numFourierCoefficients, frameFeatureDimension);
  _sinFeatures = facebook::tmk::libvec::allocateRank3(
      numPeriods, numFourierCoefficients, frameFeatureDimension);

  _pairScoreNormalizer = computePairScoreNormalizer(fourierCoefficients);
}

// ----------------------------------------------------------------
// Constructor for loading precomputed data from a file. Here it's possible for
// the dimensions to be inconsistent, so we intend this constructor to be
// private.
TMKFeatureVectors::TMKFeatureVectors(
    facebook::tmk::io::TMKFramewiseAlgorithm algorithm,
    int framesPerSecond,
    int frameFeatureCount,
    const Periods& periods,
    const FourierCoefficients& fourierCoefficients,
    const FrameFeature& pureAverageFeature,
    const FeaturesByPeriodsAndFourierCoefficients& cosFeatures,
    const FeaturesByPeriodsAndFourierCoefficients& sinFeatures)
    : _algorithm(algorithm),
      _framesPerSecond(framesPerSecond),
      _periods(periods),
      _fourierCoefficients(fourierCoefficients),

      _frameFeatureDimension(pureAverageFeature.size()),
      _frameFeatureCount(frameFeatureCount),

      _pureAverageFeature(pureAverageFeature),
      _cosFeatures(cosFeatures),
      _sinFeatures(sinFeatures),

      _pairScoreNormalizer(computePairScoreNormalizer(fourierCoefficients)) {}

// ----------------------------------------------------------------
// Supporting method for the above private constructor.  Invariants are
// documented in detail within tmkfv.h.  Recall though from there that periods
// are 1D (call it P) vector of int, fourier coefficients are 1D (call it C)
// vector of float, pure-average feature is 1D (call it D) vector of float, and
// cosine and sine features are 3D P x C x D. Note that P and/or C can be zero.
std::shared_ptr<TMKFeatureVectors> TMKFeatureVectors::tryCreateFromPrecomputed(
    facebook::tmk::io::TMKFramewiseAlgorithm algorithm,
    int framesPerSecond,
    int frameFeatureCount,
    const Periods& periods,
    const FourierCoefficients& fourierCoefficients,
    const FrameFeature& pureAverageFeature,
    const FeaturesByPeriodsAndFourierCoefficients& cosFeatures,
    const FeaturesByPeriodsAndFourierCoefficients& sinFeatures) {
  int P = periods.size();
  int C = fourierCoefficients.size();
  int D = pureAverageFeature.size();

  bool ok = facebook::tmk::libvec::checkDimensionsRank3(cosFeatures, P, C, D) &&
      facebook::tmk::libvec::checkDimensionsRank3(sinFeatures, P, C, D);

  if (ok) {
    return std::shared_ptr<TMKFeatureVectors>(new TMKFeatureVectors(
        algorithm,
        framesPerSecond,
        frameFeatureCount,
        periods,
        fourierCoefficients,
        pureAverageFeature,
        cosFeatures,
        sinFeatures));
  } else {
    return nullptr;
  }
}

// ----------------------------------------------------------------
bool TMKFeatureVectors::areCompatible(
    const TMKFeatureVectors& fva, const TMKFeatureVectors& fvb) {
  if (fva._algorithm != fvb._algorithm) {
    fprintf(
        stderr,
        "TMK: algorithm \"%s\" != \"%s\".\n",
        facebook::tmk::io::algorithmToName(fva._algorithm).c_str(),
        facebook::tmk::io::algorithmToName(fvb._algorithm).c_str());
    return false;
  }

  if (fva._framesPerSecond != fvb._framesPerSecond) {
    fprintf(
        stderr,
        "TMK: frames per second %d != %d.\n",
        fva._framesPerSecond,
        fvb._framesPerSecond);
    return false;
  }

  if (fva._periods.size() != fvb._periods.size()) {
    fprintf(
        stderr,
        "TMK: period-count %d != %d.\n",
        (int)fva._periods.size(),
        (int)fvb._periods.size());
    return false;
  }
  int np = fva._periods.size();
  for (int i = 0; i < np; i++) {
    if (fva._periods[i] != fvb._periods[i]) {
      fprintf(
          stderr,
          "TMK: period[%d] %d != %d.\n",
          i,
          fva._periods[i],
          fvb._periods[i]);
      return false;
    }
  }

  if (fva._fourierCoefficients.size() != fvb._fourierCoefficients.size()) {
    fprintf(
        stderr,
        "TMK: fourier-coefficient-count %d != %d.\n",
        (int)fva._fourierCoefficients.size(),
        (int)fvb._fourierCoefficients.size());
    return false;
  }
  for (int i = 0; i < fva._fourierCoefficients.size(); i++) {
    float ca = fva._fourierCoefficients[i];
    float cb = fvb._fourierCoefficients[i];
    float m = std::fmax(std::fabs(ca), std::fabs(cb));
    if (m > 0) {
      float relerr = std::fabs((ca - cb) / m);
      if (relerr > 1e-6) {
        fprintf(
            stderr, "TMK: fourier coefficient %d %.7e != %.7e.\n", i, ca, cb);
        return false;
      }
    }
  }

  // Should have been caught by the algorithm-magic check, but, if someone
  // generated data files with the same algorithm name and somehow different
  // frame-feature dimensions, we would want to catch that.
  if (fva._frameFeatureDimension != fvb._frameFeatureDimension) {
    fprintf(
        stderr,
        "TMK: frame-feature dimension %d != %d.\n",
        fva._frameFeatureDimension,
        fvb._frameFeatureDimension);
    return false;
  }

  return true;
}

// ----------------------------------------------------------------
// The TMK-output feature vectors are indexed by the periods T and
// the fourier-coefficient index j (0 to m-1).
// See comments in tmkfv.h for algebraic derivations.

void TMKFeatureVectors::ingestFrameFeature(
    const FrameFeature& frameFeature,
    int t // frame number
) {
  if (frameFeature.size() != _frameFeatureDimension) {
    throw std::runtime_error(
        "Incompatible frame-feature dimensions " +
        std::to_string(frameFeature.size()) + ", " +
        std::to_string(_frameFeatureDimension));
  }

  for (int k = 0; k < frameFeature.size(); k++) {
    _pureAverageFeature[k] += frameFeature[k];
  }

  FrameFeature normalizedFrameFeature(frameFeature);
  facebook::tmk::libvec::L2NormalizeVector(normalizedFrameFeature);

  for (int i = 0; i < _periods.size(); i++) {
    int T = _periods[i];

    for (int k = 0; k < normalizedFrameFeature.size(); k++) {
      _cosFeatures[i][0][k] += normalizedFrameFeature[k];
    }

    for (int j = 1; j < _fourierCoefficients.size(); j++) {
      double arg = 2.0 * pi * (double)j * (double)t / (double)T;
      double cosArg = cos(arg);
      double sinArg = sin(arg);
      for (int k = 0; k < normalizedFrameFeature.size(); k++) {
        _cosFeatures[i][j][k] += normalizedFrameFeature[k] * cosArg;
        _sinFeatures[i][j][k] += normalizedFrameFeature[k] * sinArg;
      }
    }
  }

  _frameFeatureCount++;
}

// ----------------------------------------------------------------
// See comments in tmkfv.h for algebraic derivations.
void TMKFeatureVectors::finishFrameFeatureIngest() {
  if (_frameFeatureCount > 0) {
    facebook::tmk::libvec::scalarDivide(
        _pureAverageFeature, (float)_frameFeatureCount);
    for (int i = 0; i < _periods.size(); i++) {
      for (int j = 0; j < _fourierCoefficients.size(); j++) {
        facebook::tmk::libvec::L2NormalizeVector(_cosFeatures[i][j]);
        facebook::tmk::libvec::L2NormalizeVector(_sinFeatures[i][j]);

        facebook::tmk::libvec::scalarMultiply(
            _cosFeatures[i][j], std::sqrt(_fourierCoefficients[j]));
        facebook::tmk::libvec::scalarMultiply(
            _sinFeatures[i][j], std::sqrt(_fourierCoefficients[j]));
      }
    }
  }
}

// ----------------------------------------------------------------
// Poullot parameters
// https://www.dropbox.com/s/uaav1l2hj7m6hj4/v2-circu-p381-poullot.pdf?dl=0
// TODO(T28927988) // Shigan Chu and Nathan Hurst are working on learned
// parameters which we expect to be better.
Periods TMKFeatureVectors::makePoullotPeriods() {
  return Periods{2731, 4391, 9767, 14653};
}

// ----------------------------------------------------------------
// These are the Poullot parameters as described in
// https://www.dropbox.com/s/uaav1l2hj7m6hj4/v2-circu-p381-poullot.pdf?dl=0
//
// TODO(T28927988) // Shigan Chu and Nathan Hurst are working on learned
// parameters which we expect to be better.
//
// The Poullot values are a simple formula.  Issue: can't find
// std::cyl_bessel_if et al. within C++ header libraries despite half an hour
// of googling+futzingwith.
//
// And it's not worth my time since these are just temporary until I get
// trained TMK coefficients computed -- which will (like these) just end up
// being tabulated anyway.
//
// So I might as well tabulate.
//
//  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// The C++ code I would write:
//
//   vector<float> coefficients(m);
//   float sinhBeta = sinh(beta);
//   coefficients[0] = (cyl_bessel_if(0, beta) - exp(-beta)) / (2*sinhBeta);
//   for (int i = 1; i < m; i++) {
//     coefficients[i] = cyl_bessel_if(i, beta) / sinhBeta;
//   }
//   return coefficients;
//
//  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// And the Python code:
//
//   from scipy.special import iv as bessel
//   from math import sinh, exp
//
//   m = 32
//   beta = 32
//
//   a0 = (bessel(0, beta) - exp(-beta)) / (2 * sinh(beta))
//   print 0,a0
//   for i in range(1, m):
//       ai = bessel(i, beta) / sinh(beta)
//       print i, ai

FourierCoefficients TMKFeatureVectors::makePoullotFourierCoefficients() {
  return std::vector<float>{
      0.0708041893112,   0.13937789309,     0.132897260304,
      0.122765735552,    0.109878684888,    0.09529606433,
      0.0800986647852,   0.0652590650356,   0.0515478238322,
      0.0394851531195,   0.0293374252025,   0.0211492623679,
      0.0147973073245,   0.0100512818746,   0.0066306408014,
      0.00424947117334,  0.0026467615764,   0.00160270959695,
      0.000943882629639, 0.000540841638603, 0.000301633183798,
      0.000163800158855, 8.66454753015e-05, 4.46626303151e-05,
      2.24429442235e-05, 1.09982139799e-05, 5.25823487999e-06,
      2.45358229988e-06, 1.11781474895e-06, 4.97406489221e-07,
      2.16265487234e-07, 9.19087006565e-08};
}

// ----------------------------------------------------------------
bool TMKFeatureVectors::writeToOutputStream(
    FILE* fp, const char* programName) const {
  bool write_rc = false;

  if (!facebook::tmk::io::writeFeatureVectorFileHeader(
          fp,
          _algorithm, // provenance
          _framesPerSecond, // provenance
          _periods.size(), // a.k.a. P
          _fourierCoefficients.size(), // a.k.a m
          _frameFeatureDimension, // a.k.a d
          _frameFeatureCount, // informational: frame count (time-resampled)
          programName)) { // ... in the hashed video
    perror("fwrite");
    return false;
  }

  write_rc = facebook::tmk::io::writeIntVector(_periods, fp);
  if (!write_rc) {
    fprintf(stderr, "%s: failed to write periods vector.\n", programName);
    return false;
  }

  write_rc = facebook::tmk::io::writeFloatVector(_fourierCoefficients, fp);
  if (!write_rc) {
    fprintf(
        stderr,
        "%s: failed to write fourier-coefficients feature vector.\n",
        programName);
    return false;
  }

  write_rc = facebook::tmk::io::writeFloatVector(_pureAverageFeature, fp);
  if (!write_rc) {
    fprintf(
        stderr,
        "%s: failed to write pure-average feature vector.\n",
        programName);
    return false;
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  for (int i = 0; i < _periods.size(); i++) {
    for (int j = 0; j < _fourierCoefficients.size(); j++) {
      write_rc = facebook::tmk::io::writeFloatVector(_cosFeatures[i][j], fp);
      if (!write_rc) {
        fprintf(
            stderr, "%s: failed to write feature vector %d.\n", programName, 0);
        return false;
      }
    }
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  for (int i = 0; i < _periods.size(); i++) {
    for (int j = 0; j < _fourierCoefficients.size(); j++) {
      write_rc = facebook::tmk::io::writeFloatVector(_sinFeatures[i][j], fp);
      if (!write_rc) {
        fprintf(
            stderr, "%s: failed to write feature vector %d.\n", programName, 0);
        return false;
      }
    }
  }

  return true;
}

// ----------------------------------------------------------------
bool TMKFeatureVectors::writeToOutputFile(
    const char* fileName, const char* programName) const {
  FILE* fp = fopen(fileName, "wb");
  if (fp == nullptr) {
    perror("fopen");
    fprintf(
        stderr,
        "%s: could not open \"%s\" for write.\n",
        programName,
        fileName);
    return false;
  }
  bool rc = writeToOutputStream(fp, programName);
  if (fclose(fp) != 0) {
    perror("fclose");
    fprintf(
        stderr,
        "%s: could not close \"%s\" after write.\n",
        programName,
        fileName);
    return false;
  }
  return rc;
}

// ----------------------------------------------------------------
std::shared_ptr<TMKFeatureVectors> TMKFeatureVectors::readFromInputStream(
    FILE* fp, const char* programName) {
  io::FeatureVectorFileHeader header;
  bool read_rc;

  facebook::tmk::io::TMKFramewiseAlgorithm algorithm;
  if (!facebook::tmk::io::readFeatureVectorFileHeader(
          fp, &header, algorithm, programName)) {
    return nullptr;
  }

  if (algorithm == facebook::tmk::io::TMKFramewiseAlgorithm::UNRECOGNIZED) {
    fprintf(stderr, "%s: failed to recognized algorithm.\n", programName);
    return nullptr;
  }
  int framesPerSecond = header.framesPerSecond;
  int numPeriods = header.numPeriods;
  int numFourierCoefficients = header.numFourierCoefficients;
  int frameFeatureDimension = header.frameFeatureDimension;
  int frameFeatureCount = header.frameFeatureCount;
  Periods periods(numPeriods);
  FourierCoefficients fourierCoefficients(numFourierCoefficients);
  FrameFeature pureAverageFeature(frameFeatureDimension);

  // TODO(T25190142): include frameCount

  bool eofUnusedHere = false;

  read_rc = facebook::tmk::io::readIntVector(periods, fp);
  if (!read_rc) {
    fprintf(stderr, "%s: failed to read periods vector.\n", programName);
    return nullptr;
  }

  read_rc = facebook::tmk::io::readFloatVector(
      fourierCoefficients, fp, eofUnusedHere);
  if (!read_rc) {
    fprintf(
        stderr,
        "%s: failed to read fourier-coefficients feature vector.\n",
        programName);
    return nullptr;
  }

  read_rc =
      facebook::tmk::io::readFloatVector(pureAverageFeature, fp, eofUnusedHere);
  if (!read_rc) {
    fprintf(
        stderr,
        "%s: failed to read pure-average feature vector.\n",
        programName);
    return nullptr;
  }

  FeaturesByPeriodsAndFourierCoefficients cosFeatures =
      facebook::tmk::libvec::allocateRank3(
          numPeriods, numFourierCoefficients, frameFeatureDimension);
  FeaturesByPeriodsAndFourierCoefficients sinFeatures =
      facebook::tmk::libvec::allocateRank3(
          numPeriods, numFourierCoefficients, frameFeatureDimension);

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  for (int i = 0; i < cosFeatures.size(); i++) {
    for (int j = 0; j < cosFeatures[i].size(); j++) {
      read_rc = facebook::tmk::io::readFloatVector(
          cosFeatures[i][j], fp, eofUnusedHere);
      if (!read_rc) {
        fprintf(
            stderr, "%s: failed to read feature vector %d.\n", programName, 0);
        return nullptr;
      }
    }
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  for (int i = 0; i < sinFeatures.size(); i++) {
    for (int j = 0; j < sinFeatures[i].size(); j++) {
      read_rc = facebook::tmk::io::readFloatVector(
          sinFeatures[i][j], fp, eofUnusedHere);
      if (!read_rc) {
        fprintf(
            stderr, "%s: failed to read feature vector %d.\n", programName, 0);
        return nullptr;
      }
    }
  }

  return tryCreateFromPrecomputed(
      algorithm,
      framesPerSecond,
      frameFeatureCount,
      periods,
      fourierCoefficients,
      pureAverageFeature,
      cosFeatures,
      sinFeatures);
}

// ----------------------------------------------------------------
std::shared_ptr<TMKFeatureVectors> TMKFeatureVectors::readFromInputFile(
    const char* fileName, const char* programName) {
  FILE* fp = fopen(fileName, "rb");
  if (fp == nullptr) {
    perror("fopen");
    fprintf(
        stderr, "%s: could not open \"%s\" for read.\n", programName, fileName);
    return nullptr;
  }

  auto pfv = readFromInputStream(fp, programName);

  (void)fclose(fp);
  return pfv;
}

// ----------------------------------------------------------------
void TMKFeatureVectors::L2NormalizePureAverageFeature() {
  facebook::tmk::libvec::L2NormalizeVector(_pureAverageFeature);
}

// ----------------------------------------------------------------
// See comments in tmkfv.h for algebraic derivations.

void TMKFeatureVectors::findPairOffsetsModuloPeriods(
    const TMKFeatureVectors& fva,
    const TMKFeatureVectors& fvb,
    BestOffsets& bestOffsets,
    ValuesAtBestOffsets& valuesAtBestOffsets,
    bool printDetails) {
  int numPeriods = fva._periods.size();
  int numFourierCoefficients = fva._fourierCoefficients.size();

  // We assume areCompatible has already been called on fva and fvb.
  bestOffsets = BestOffsets(numPeriods);
  valuesAtBestOffsets = ValuesAtBestOffsets(numPeriods);

  if (numPeriods == 0 || numFourierCoefficients == 0) {
    return;
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // We assume all cos/sin features are already L2-normalized.

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  std::vector<std::vector<float>> dotCosCos =
      facebook::tmk::libvec::allocateRank2(numPeriods, numFourierCoefficients);
  std::vector<std::vector<float>> dotSinSin =
      facebook::tmk::libvec::allocateRank2(numPeriods, numFourierCoefficients);
  std::vector<std::vector<float>> dotSinCos =
      facebook::tmk::libvec::allocateRank2(numPeriods, numFourierCoefficients);
  std::vector<std::vector<float>> dotCosSin =
      facebook::tmk::libvec::allocateRank2(numPeriods, numFourierCoefficients);

  for (int i = 0; i < numPeriods; i++) {
    for (int j = 0; j < numFourierCoefficients; j++) {
      const std::vector<float>& fvaCos = fva._cosFeatures[i][j];
      const std::vector<float>& fvaSin = fva._sinFeatures[i][j];
      const std::vector<float>& fvbCos = fvb._cosFeatures[i][j];
      const std::vector<float>& fvbSin = fvb._sinFeatures[i][j];
      dotCosCos[i][j] = facebook::tmk::libvec::computeDot(fvaCos, fvbCos);
      dotSinSin[i][j] = facebook::tmk::libvec::computeDot(fvaSin, fvbSin);
      dotSinCos[i][j] = facebook::tmk::libvec::computeDot(fvaSin, fvbCos);
      dotCosSin[i][j] = facebook::tmk::libvec::computeDot(fvaCos, fvbSin);
    }
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  for (int i = 0; i < numPeriods; i++) {
    int period = fva._periods[i];
    std::vector<float> K_deltas(period);
    for (int offset = 0; offset < period; offset++) {
      float delta = 2.0 * pi * (float)offset / (float)period;
      float K_delta = dotCosCos[i][0];
#if 0
      // Direct evaluation
      for (int j = 1; j < numFourierCoefficients; j++) {
        K_delta += cos(j * delta) * (dotCosCos[i][j] + dotSinSin[i][j]);
        K_delta += sin(j * delta) * (dotSinCos[i][j] - dotCosSin[i][j]);
      }
#else
      /**
       * We noticed that sin and cos were the dominant cost to this function.
       * We can try using an incremental algorithm for equally spaced exp(1j)
       * as recommended in Numerical Recipes. A good demonstration of precision:
       * http://steve.hollasch.net/cgindex/math/inccos.html
       * this is based on the addition formulae.  We replace cos(d) with
       * sin(d/2) to avoid truncation error using the double angle formula.
       *
       * Initial tests show 1/3 improvement in performance.
       **/

      float cos_jd = 1;
      float sin_jd = 0;

      float beta = sin(delta);
      float alpha = sin(delta / 2);
      alpha = 2 * alpha * alpha;

      for (int j = 1; j < numFourierCoefficients; j++) {
        // a bit magical because we're starting at j = 1
        float n_cos_jd = (alpha * cos_jd) + (beta * sin_jd);
        float n_sin_jd = (alpha * sin_jd) - (beta * cos_jd);

        cos_jd -= n_cos_jd;
        sin_jd -= n_sin_jd;

        K_delta += cos_jd * (dotCosCos[i][j] + dotSinSin[i][j]);
        K_delta += sin_jd * (dotSinCos[i][j] - dotCosSin[i][j]);
      }
#endif
      if (printDetails) {
        printf("TODK %d %d %.6f %.6f\n", period, offset, delta, K_delta);
      }
      K_deltas[offset] = K_delta;
    }

    // Now find the offset with the largest K_delta for this period.
    // This is the best alignment of the two videos modulo this period.
    float max_K_delta = K_deltas[0];
    float maxIndex = 0;
    for (int offset = 1; offset < period; offset++) {
      if (K_deltas[offset] > max_K_delta) {
        max_K_delta = K_deltas[offset];
        maxIndex = offset;
      }
    }
    bestOffsets[i] = maxIndex;
    valuesAtBestOffsets[i] = max_K_delta;
  }
}

// ----------------------------------------------------------------
float TMKFeatureVectors::computeLevel1Score(
    const TMKFeatureVectors& fva, const TMKFeatureVectors& fvb) {
  return facebook::tmk::libvec::computeCosSim(
      fva.getPureAverageFeature(), fvb.getPureAverageFeature());
}

// ----------------------------------------------------------------
float TMKFeatureVectors::computeLevel2Score(
    const TMKFeatureVectors& fva, const TMKFeatureVectors& fvb) {
  BestOffsets bestOffsets;
  ValuesAtBestOffsets valuesAtBestOffsets;
  TMKFeatureVectors::findPairOffsetsModuloPeriods(
      fva, fvb, bestOffsets, valuesAtBestOffsets, false);
#if 1
  return facebook::tmk::libvec::computeMax(valuesAtBestOffsets) /
      fva._pairScoreNormalizer;
#else
  return facebook::tmk::libvec::computeSum(valuesAtBestOffsets) /
      pva.getNumPeriods / fva._pairScoreNormalizer;
#endif
}

// ----------------------------------------------------------------
bool TMKFeatureVectors::compare(
    const TMKFeatureVectors& fva,
    const TMKFeatureVectors& fvb,
    float tolerance) {
  if (TMKFeatureVectors::areCompatible(fva, fvb)) {
    if (facebook::tmk::libvec::compareVectors(
            fva._pureAverageFeature, fvb._pureAverageFeature, tolerance)) {
      bool cos_equal = facebook::tmk::libvec::compareVectorsRank3(
          fva._cosFeatures, fvb._cosFeatures, tolerance);
      bool sin_equal = facebook::tmk::libvec::compareVectorsRank3(
          fva._sinFeatures, fvb._sinFeatures, tolerance);
      return cos_equal && sin_equal;
    }
    return false;
  }
  return false;
}

} // namespace algo
} // namespace tmk
} // namespace facebook
