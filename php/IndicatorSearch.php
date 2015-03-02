<?php
/*
 *  Copyright (c) 2014, Facebook, Inc.
 *  All rights reserved.
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

final class IndicatorSearch extends BaseSearch {

  public function getAdditionalOptions() {
    return array (
      'b' => 'type',
    );
  }

  public function getEndpoint() {
    return '/threat_indicators';
  }

  public function getUsage() {
    return "\t-b type of indicators to search for (optional, see API docs for ".
        "full list)\n".
      "\t-m strict match the query string (optional)\n".
      "\t-q query string\n".
      "\t-s beginning timestamp or date time string for a time windowed query\n".
      "\t-u ending timestamp or date time string for a time windowed query\n";
  }

  public function getResultsAsCSV($results) {
    $csv = "# ThreatExchange Results - queried at ".time()."\n".
      "id,type,indicator,is_malicious,severity\n";
    foreach ($results as $result) {
      $row = array(
        $result['id'],
        $result['type'],
        $result['indicator'],
        $result['malicious'],
        $result['severity'],
      );
      $csv .= implode(',', $row)."\n";
    }
    return $csv;
  }
}
