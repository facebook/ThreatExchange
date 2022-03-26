#ifndef TMK_QUERY_H
#define TMK_QUERY_H

#include <tmk/cpp/algo/tmkfv.h>
using namespace facebook::tmk::algo;

void handleListFileNameOrDie(
    const char* argv0,
    const char* listFileName,
    std::map<std::string, std::shared_ptr<TMKFeatureVectors>>&
        metadataToFeatures);

void handleListFpOrDie(
    const char* argv0,
    FILE* listFp,
    std::map<std::string, std::shared_ptr<TMKFeatureVectors>>&
        metadataToFeatures);

void handleTmkFileNameOrDie(
    const char* argv0,
    const char* tmkFileName,
    std::map<std::string, std::shared_ptr<TMKFeatureVectors>>&
        metadataToFeatures);

int tmkQuery(
    int argc,
    char** argv);

#endif
