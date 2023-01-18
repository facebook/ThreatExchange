<?php

// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

require 'pdqhasher.php';

$filenames = array_slice($argv, 1);
if (empty($filenames)) {
  fprintf(STDERR, "%s: need at least one image file name.\n", $argv[0]);
  exit(1);
}

foreach ($filenames as $filename) {

  list ($hashes, $quality) = PDQHasher::computeHashesAndQualityFromFilename($filename);
  foreach ($hashes as $type => $hash) {
    $s = $hash->toHexString();
    echo "$s,$type,$quality,purephp,$filename\n";
  }

  list ($hashes, $quality) = PDQHasher::computeStringHashesAndQualityFromFilenameUsingExtension($filename);
  foreach ($hashes as $type => $hash) {
    echo "$hash,$type,$quality,extnphp,$filename\n";
  }

}
