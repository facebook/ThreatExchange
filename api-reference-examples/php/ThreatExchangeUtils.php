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

class ThreatExchangeUtils {

  private static $debugMode = false;

  public static function setDebugMode($debug_mode) {
    self::$debugMode = $debug_mode;
  }

  public static function isDebugMode() {
    return self::$debugMode;
  }

  /**
   * @throws Exceptions
   */
  public static function parseQueryFile($query_file) {
    if (!file_exists($query_file)) {
      throw new Exception(
        "ERROR: Unable to find/read query file '$query_file'\n"
      );
    }
    $fh = fopen($query_file, "r");
    $queries = array();
    while (($row = fgetcsv($fh)) !== FALSE) {
      if (!count($row) || (count($row) === 1 && !trim($row[0]))) {
        continue; // skip empty rows / queries
      }
      if (strpos($row[0], '#') === 0) {
        continue; // skip lines with comments
      }
      $queries[] = trim($row[0]);
    }
    return $queries;
  }

  /**
   * @throws Exception
   */
  public static function makeCurlRequest($uri) {
    $curler = curl_init($uri);
    curl_setopt($curler, CURLOPT_RETURNTRANSFER, true);
    $raw_json = curl_exec($curler);
    self::checkCurlResults($curler, $raw_json);
    curl_close($curler);

    if (self::isDebugMode()) {
      $json_ar = json_decode($json_string, true /* assoc array */);
      self::debugPrettyPrint($json_ar);
    }
    return $raw_json;
  }

  /**
   * @throws Exception
   */
  public static function makeCurlPostRequest($uri, $post_data) {
    $curler = curl_init($uri);
    curl_setopt($curler, CURLOPT_POST, true);
    curl_setopt($curler, CURLOPT_POSTFIELDS, http_build_query($post_data));
    curl_setopt($curler, CURLOPT_RETURNTRANSFER, true);
    $raw_json = curl_exec($curler);
    self::checkCurlResults($curler, $raw_json);
    curl_close($curler);

    if (self::isDebugMode()) {
      $json_ar = json_decode($raw_json, true /* assoc array */);
      self::debugPrettyPrint($json_ar);
    }
    return $raw_json;
  }

  /**
   * @throws Exception
   */
  protected function checkCurlResults($curler, $results) {
    $return_code = curl_getinfo($curler, CURLINFO_HTTP_CODE);
    if ($return_code !== 200) {
      throw new Exception(
        "CURL ERROR: $return_code, ".
        curl_error($curler).' - '.
        $results
      );
    }
  }

  public static function debugPrettyPrint($object) {
    var_dump($object);
  }

}
