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

abstract class BaseUpload {

  private $fields = null;

  public abstract function getEndpoint();

  protected abstract function getTypeSpecificFields();

  protected abstract function getPostDataFromCSV($data_row);

  public function getFields() {
    if (!$this->fields) {
      $this->fields = array(
        'confidence',
        'description',
        'privacy_type',
        'privacy_members',
        'severity',
        'share_level',
        'status',
      );
      $this->fields = array_merge(
        $this->fields,
        $this->getTypeSpecificFields()
      );
    }
    return $this->fields;
  }

  public static function getUploader($name) {
    switch ($name) {
      case 'indicators':
        return new IndicatorUpload();
      case 'malware':
      case 'families':
        throw new Exception(
          'Malware and Malware Family uploads are not supported yet.'
        );
      default:
        throw new Exception(
          'Search type (-t) must be one of: families, indicators or malware'
        );
    }
  }

  public function getUsage() {
    return "\t-f file containing data to upload (CSV format)\n".
      "\t-d default description, if none provided\n".
      "\t-g tag to prepend to all descriptions\n".
      "\t-m default members for privacy, if none provided\n".
      "\t-p default privacy, if none provided\n";
  }

  public function hasValidOptions($options) {
    return !isset($options['h']) && isset($options['f']);
  }

  public function parseDataFile($file_name, $options) {
    if (!file_exists($file_name)) {
      throw new Exception(
        "ERROR: Unable to find/read file '$file_name'\n"
      );
    }
    $fh = fopen($file_name, "r");
    $header = null;
    $entries = array();
    $def_privacy_data = $this->getPrivacyDataFromOptions($options);
    $def_description = (isset($options['d']))
      ? $options['d']
      : 'No description provided';
    $def_tag = (isset($options['g'])) ? $options['g'] : '';
    while (($row = fgetcsv($fh)) !== FALSE) {
      if (!count($row) || (count($row) === 1 && !trim($row[0]))) {
        continue; // skip empty rows / queries
      }
      if (strpos($row[0], '#') === 0) {
        continue; // skip lines with comments
      }

      if (!$header) {
        $header = $row;
        continue;
      }

      $post_data = $this->getPostDataFromCSV(array_combine($header, $row));

      // fold in the defaults provided
      if (!isset($post_data['description'])) {
        $post_data['description'] = $def_description;
      }
      if ($def_tag) {
        $post_data['description'] = '['.$def_tag.'] '.$post_data['description'];
      }
      if (!isset($post_data['privacy_type']) && count($def_privacy_data) > 0) {
        $post_data = array_merge($post_data, $def_privacy_data);
      }

      $entries[] = $post_data;
    }
    return $entries;
  }

  private function getPrivacyDataFromOptions($options) {
    $privacy_data = array();
    if (isset($options['p'])) {
      switch(strtoupper(trim($options['p']))) {
        case 'HAS_WHITELIST':
        case 'WHITELIST':
          $privacy_data['privacy_type'] = 'HAS_WHITELIST';
          break;
        default:
          throw new Exception(
            'You must set a privacy type!'
          );
          break;
      }
    }
    if (isset($options['m'])) {
      $privacy_data['privacy_members'] = $options['m'];
    }
    return $privacy_data;
  }

  public function buildAPIUploadRequest() {
    $uri = ThreatExchangeConfig::FACEBOOK_SERVER.$this->getEndpoint().'/?';

    // build the param array
    $params = array (
      'access_token' => ThreatExchangeConfig::getAccessToken(),
    );
    $param_str = http_build_query($params);
    $uri .= $param_str;

    return $uri;
  }

  public function getResultsAsCSV($results) {
    $csv = "# ThreatExchange Results - uploaded at ".strftime('%F %T (%z)').
      "\nid,error\n";
    foreach ($results as $result) {
      $csv .= isset($result['id']) ? $result['id'] : 'NO_ID';
      $csv .= ',';
      $csv .= isset($result['error']) ? $result['error'] : 'OK';
      $csv .= "\n";
    }
    return $csv;
  }
}
