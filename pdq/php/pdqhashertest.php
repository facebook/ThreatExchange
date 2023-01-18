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
$show_timings = false;
//$show_timings = true;
$dump = false;

$downsample = false;

foreach ($filenames as $filename) {

  list ($hash, $quality) = PDQHasher::computeHashAndQualityFromFilename($filename, $show_timings, $dump, $downsample);
  $s = $hash->toHexString();
  echo "$s,$quality,purephp,$filename\n";
  if (function_exists('pdq_compute_string_hash_and_quality_from_image_resource')) {
    list ($hash, $quality) = PDQHasher::computeStringHashAndQualityFromFilenameUsingExtension($filename, $show_timings, $dump);
    echo "$hash,$quality,extnphp,$filename\n";
  } else {
    echo "php extension not available";
  }

}
