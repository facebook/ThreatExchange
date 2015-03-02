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
 * EDIT THE VALUES IN APP_ID and APP_SECRET BEFORE CONTINUING!!!
 * VALUES FOR BOTH ARE AVAILABLE BY GOING TO
 * https://developers.facebook.com/apps/
 */
class ThreatExchangeConfig {

  const APP_ID = 0;
  const APP_SECRET = 'secret';

  const FACEBOOK_SERVER = 'https://graph.facebook.com';

  public static function getAppID() {
    if (!self::APP_ID) {
      throw new Exception(
        'Edit the APP_ID field in ThreatExchangeConfig before continuing!'
      );
    }
    return self::APP_ID;
  }

  public static function getAppSecret() {
    if (!self::APP_SECRET) {
      throw new Exception(
        'Edit the APP_SECRET field in ThreatExchangeConfig before continuing!'
      );
    }
    return self::APP_SECRET;
  }

  public static function getAccessToken() {
    return self::getAppID().'|'.self::getAppSecret();
  }

  public static function init() {
    // bootstraping method, just used right now to force load of __autoload()
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

