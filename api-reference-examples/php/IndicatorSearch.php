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

final class IndicatorSearch extends BaseSearch {

  public function getAdditionalOptions() {
    return array (
      'b' => 'type',
      'o' => 'owner',
      'r' => 'threat_type',
    );
  }

  public function getEndpoint() {
    return '/threat_descriptors';
  }

  public function getUsage() {
    return "\t-b type of indicators to search for (optional, see API docs for ".
        "full list)\n".
      "\t-m strict match the query string (optional)\n".
      "\t-o the ThreatExchange ID of the owner (optional)\n".
      "\t-r the threat type to search for (optional)\n".
      "\t-q query string\n".
      "\t-s beginning timestamp or date time string for a time windowed query\n".
      "\t-u ending timestamp or date time string for a time windowed query\n";
  }

  public function getResultsAsCSV($results) {
    $csv = "# ThreatExchange Results - queried at ".strftime('%c')."\n".
      "id,type,indicator,status,description,threat_type,owner,owner_name\n";
    foreach ($results as $result) {
      $row = array(
        $result ['id'],
	isset ( $result ['indicator'] ) ? $result ['indicator'] ['type'] : '',
	isset ( $result ['indicator'] ) ? $result ['indicator'] ['indicator'] : '',
	isset ( $result ['status'] ) ? $result ['status'] : '',
	isset ( $result ['description'] ) ? $result ['description'] : '',
	isset ( $result ['threat_type'] ) ? $result ['threat_type'] : '',
	isset ( $result ['owner'] ) ? $result ['owner'] ['id'] : '',
	isset ( $result ['owner'] ) ? $result ['owner'] ['name'] : ''
      );
      $csv .= implode(',', $row)."\n";
    }
    return $csv;
  }
}
