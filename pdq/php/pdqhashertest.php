<?php
// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

require 'pdqhasher.php';

$filenames = array_slice($argv, 1);
if (empty($filenames)) {
  fprintf(STDERR, "%s: need at least one image file name.\n", $argv[0]);
  exit(1);
}
$show_timings = false;
//$show_timings = true;
$dump = false;

foreach ($filenames as $filename) {

  list ($hash, $quality) = PDQHasher::computeHashAndQualityFromFilename($filename, $show_timings, $dump);
  $s = $hash->toHexString();
  echo "$s,$quality,purephp,$filename\n";

  list ($hash, $quality) = PDQHasher::computeStringHashAndQualityFromFilenameUsingExtension($filename, $show_timings, $dump);
  echo "$hash,$quality,extnphp,$filename\n";

}
