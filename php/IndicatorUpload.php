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

final class IndicatorUpload extends BaseUpload {

  public function getEndpoint() {
    return '/threat_descriptors';
  }

  protected function getTypeSpecificFields() {
    return array(
      'expired_on',
      'indicator',
      'passwords',
      'type',
      'threat_type',
    );
  }

  protected function getPostDataFromCSV($data_row) {
    $post_data = array();
    foreach ($this->getFields() as $field_name) {
      if (isset($data_row[$field_name]) &&
          $data_row[$field_name] !== '' &&
          $data_row[$field_name] !== null) {
        $post_data[$field_name] = $data_row[$field_name];
      }
    }
    return $post_data;
  }
}
