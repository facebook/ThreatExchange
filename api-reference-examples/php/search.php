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
$options = getopt('b:f:hmq:s:u:t:');
if (!isset($options['t'])) {
  echo print_usage();
  exit(1);
}

// Load user details
$app_id = ThreatExchangeConfig::getAppID();
$app_secret = ThreatExchangeConfig::getAppSecret();

$searcher = BaseSearch::getSearcher($options['t']);
if (!$searcher->hasValidOptions($options)) {
  echo print_usage().$searcher->getUsage();
  exit(1);
}

// Build query sets
$requests = array();
if (isset($options['q']) ||
    (isset($options['s']) && isset($options['u']))) {
  $requests[] = $searcher->buildAPIRequest($options);
} else if (isset($options['f'])) {
  $queries = ThreatExchangeUtils::parseQueryFile($options['f']);
  foreach ($queries as $query) {
    $options['q'] = $query;
    $requests[] = $searcher->buildAPIRequest($options);
  }
} else {
  echo print_usage().$searcher->getUsage();
  exit(1);
}

// make the requests via Curl
$results = array();
foreach ($requests as $request) {
  try {
    $raw_result = ThreatExchangeUtils::makeCurlRequest($request);
    $json = json_decode(
      $raw_result,
      true,
      512,
      JSON_BIGINT_AS_STRING
    );
    if (isset($json['data'])) {
      $results = array_merge($results, $json['data']);
    }
  } catch (Exception $e) {
    echo $e->getMessage()."\n";
    exit(1);
  }
}
echo $searcher->getResultsAsCSV($results)."\n";

function print_usage() {
  return "usage: php threat_exchange/search/search.php\n".
    "\t-t search type, one of: 'families', 'indicators', or 'malware'\n".
    "\t-f query file (optional, use to bulk search instead of using -q)\n";
}
