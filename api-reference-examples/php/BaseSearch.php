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

abstract class BaseSearch {

  public abstract function getEndpoint();

  public abstract function getResultsAsCSV($results);

  public static function getSearcher($name) {
    switch ($name) {
      case 'malware':
        return new MalwareSearch();
      case 'families':
        return new MalwareFamilySearch();
      case 'indicators':
        return new IndicatorSearch();
      default:
        throw new Exception(
          'Search type (-t) must be one of: families, indicators or malware'
        );
    }
  }

  public function getUsage() {
    return "\t-q query string\n".
      "\t-m strict match the query string (optional)\n".
      "\t-s beginning timestamp or date time string for a time windowed query\n".
      "\t-u ending timestamp or date time string for a time windowed query\n";
  }

  public function getOptions() {
    $options = array(
      'm' => 'strict_text',
      'q' => 'text',
      's' => 'since',
      'u' => 'until',
    );
    return array_merge($options, $this->getAdditionalOptions());
  }

  public function hasValidOptions($options) {
    if (isset($options['h'])) {
      return false;
    } else if (!(isset($options['q']) xor isset($options['f'])) &&
               !isset($options['s']) &&
               !isset($options['u'])) {
      return false;
    }
    return true;
  }

  public function getAdditionalOptions() {
    return array();
  }

  public function buildAPIRequest($query_params, $optional_params=array()) {
    $uri = ThreatExchangeConfig::FACEBOOK_SERVER.$this->getEndpoint().'/?';

    // build the param array
    $params = array (
      'access_token' => ThreatExchangeConfig::getAccessToken(),
    );

    if (isset($query_params['q'])) {
      $params['text'] = $query_params['q'];
    }
    if (isset($query_params['m'])) {
      $params['strict_text'] = true;
    }
    if (isset($query_params['s'])) {
      $params['since'] = $query_params['s'];
    }
    if (isset($query_params['u'])) {
      $params['until'] = $query_params['u'];
    }

    foreach ($optional_params as $cli_opt => $param_name) {
      if (isset($query_params[$cli_opt])) {
        $params[$param_name] = $query_params[$cli_opt];
      }
    }

    $param_str = http_build_query($params);
    $uri .= $param_str;

    return $uri;
  }
}
