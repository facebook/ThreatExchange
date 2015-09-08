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

/**
 * SET YOUR TX_APP_ID and TX_APP_SECRET ENV VARIABLES BEFORE CONTINUING!!!
 * VALUES FOR BOTH ARE AVAILABLE BY GOING TO
 * https://developers.facebook.com/apps/
 */
class ThreatExchangeConfig {

  const FACEBOOK_SERVER = 'https://graph.facebook.com/v2.4';

  private static $appID = 0;
  private static $appSecret = null;

  public static function getAppID() {
    if (!self::$appID) {
      throw new Exception(
        'Set the TX_APP_ID environment variable before continuing!'
      );
    }
    return self::$appID;
  }

  public static function getAppSecret() {
    if (!self::$appSecret) {
      throw new Exception(
        'Set the TX_APP_SECRET environment variable before continuing!'
      );
    }
    return self::$appSecret;
  }

  public static function getAccessToken() {
    return self::getAppID().'|'.self::getAppSecret();
  }

  public static function init() {
    // bootstraping method, forces call to __autoload()

    // load credentials from system environment variables
    self::$appID = $_ENV['TX_APP_ID'];
    self::$appSecret = $_ENV['TX_APP_SECRET'];
  }
}

/**
 * Handles auto-loading of PHP classes
 *
 * @see http://us1.php.net/manual/en/language.oop5.autoload.php
 */
function __autoload($class) {
  $dirs = array (
      __ROOT__,
      __ROOT__.'/search',
  );

  foreach ($dirs as $dir) {
    if (file_exists($dir.'/'.$class.'.php')) {
      require_once($dir.'/'.$class.'.php');
      return;
    }
  }
  throw new Exception('ERROR: Unable to load '.$class.' make sure the '.
    'directory where the class resides is listed in __autoload() in '.
    __ROOT__.'/'.__FILE__
  );
}
