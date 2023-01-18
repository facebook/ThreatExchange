<?php
/*
 *  Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 *  This source code is licensed under the BSD-style license found in the
 *  LICENSE file in the root directory of this source tree. An additional grant
 *  of patent rights can be found in the PATENTS file in the same directory.
 *
 */

if (!defined('__ROOT__')) {
  define('__ROOT__', realpath(dirname(__FILE__)));
}
require_once(__ROOT__.'/ThreatExchangeConfig.php');
ThreatExchangeConfig::init();

// Get the command line options
$options = getopt('d:f:g:hm:p:t:');
if (isset($options['h']) || !isset($options['t'])) {
  echo print_usage();
  exit(1);
}

// Load user details
$app_id = ThreatExchangeConfig::getAppID();
$app_secret = ThreatExchangeConfig::getAppSecret();

$uploader = BaseUpload::getUploader($options['t']);
if (!$uploader->hasValidOptions($options)) {
  echo print_usage().$uploader->getUsage();
  exit(1);
}

// Build POST data sets
$entries = $uploader->parseDataFile($options['f'], $options);

// make the requests via Curl
$results = array();
foreach ($entries as $request_uri => $post_data) {
  try {
    echo "Calling $request_uri with ".implode(',',$post_data)."\n";
    $raw_result = ThreatExchangeUtils::makeCurlPostRequest(
      $uploader->buildAPIUploadRequest(),
      $post_data
    );
    $json = json_decode(
      $raw_result,
      true,
      512,
      JSON_BIGINT_AS_STRING
    );
    $results[] = $json;
  } catch (Exception $e) {
    echo $e->getMessage()."\n";
  }
}
echo $uploader->getResultsAsCSV($results)."\n";

function print_usage() {
  return "usage: php threat_exchange/upload.php\n".
    "\t-t upload type, one of: 'families', 'indicators', or 'malware'\n".
    BaseUpload::getUsage();
}
