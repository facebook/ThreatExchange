#include <pdq/cpp/io/hashio.h>
#include <vpdq/cpp/hashing/vpdqHashType.h>
#include <vpdq/cpp/io/vpdqio.h>

using namespace std;

namespace facebook {
namespace vpdq {
namespace hashing {
bool matchTwoHashBrute(
    vector<vpdq::hashing::vpdqFeature> qHashes,
    vector<vpdq::hashing::vpdqFeature> tHashes,
    int distanceTolerance,
    int qualityTolerance,
    double& qMatch,
    double& tMatch,
    bool verbose) {
  vector<vpdq::hashing::vpdqFeature> queryFiltered, targetFiltered;
  size_t i = 0, j = 0;
  int qMatchCnt = 0;
  int tMatchCnt = 0;
  for (i = 0; i < qHashes.size(); i++) {
    if (qHashes[i].quality >= qualityTolerance) {
      queryFiltered.push_back(qHashes[i]);
    } else if (verbose) {
      printf(
          "Skipping Line %zu Skipping Query Hash: %s, because of low quality Query Hash: %d \n",
          i,
          qHashes[i].pdqHash.format().c_str(),
          qHashes[i].quality);
    }
  }
  for (i = 0; i < tHashes.size(); i++) {
    if (tHashes[i].quality >= qualityTolerance) {
      targetFiltered.push_back(tHashes[i]);
    } else if (verbose) {
      printf(
          "Skipping Line %zu Skipping Target Hash: %s, because of low quality Target Hash: %d \n",
          i,
          tHashes[i].pdqHash.format().c_str(),
          tHashes[i].quality);
    }
  }

  for (i = 0; i < queryFiltered.size(); i++) {
    for (j = 0; j < targetFiltered.size(); j++) {
      if (queryFiltered[i].pdqHash.hammingDistance(targetFiltered[j].pdqHash) <
          distanceTolerance) {
        qMatchCnt++;
        if (verbose) {
          printf(
              "Query Hash: %s Target Hash: %s match \n",
              queryFiltered[i].pdqHash.format().c_str(),
              targetFiltered[j].pdqHash.format().c_str());
        }
        break;
      }
    }
  }
  for (i = 0; i < targetFiltered.size(); i++) {
    for (j = 0; j < queryFiltered.size(); j++) {
      if (targetFiltered[i].pdqHash.hammingDistance(queryFiltered[j].pdqHash) <
          distanceTolerance) {
        tMatchCnt++;
        if (verbose) {
          printf(
              "Query Hash: %s Target Hash: %s match \n",
              queryFiltered[j].pdqHash.format().c_str(),
              targetFiltered[i].pdqHash.format().c_str());
        }
        break;
      }
    }
  }
  qMatch = (float)qMatchCnt * 100 / queryFiltered.size();
  tMatch = (float)tMatchCnt * 100 / targetFiltered.size();
  return true;
}
} // namespace hashing
} // namespace vpdq
} // namespace facebook
