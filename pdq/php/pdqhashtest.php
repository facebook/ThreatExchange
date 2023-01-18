<?php

// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

require 'pdqhash.php';

if (count($argv) > 1) {
  fprintf(STDERR, "%s: takes no arguments.\n", $argv[0]);
  exit(1);
}

$hash = PDQHash::makeZeroesHash();
$s = $hash->toHexString();
echo "s=$s\n";
for ($i = 0; $i < 256; $i++) {
  $hash->setBit($i);
  $s = $hash->toHexString();
  $n = $hash->hammingNorm();
  echo "s=$s n=$n\n";
}
$s = 'f8f8f0cce0f4e84d0e370a22028f67f0b36e2ed596623e1d33e6339c4e9c9b22';
echo "s=$s\n";
$hash = PDQHash::fromHexString($s);
$s = $hash->toHexString();
echo "s=$s\n";

$strings = $hash->to16BitStrings();
echo "\n";
foreach ($strings as $string) {
  echo "$string\n";
}

$strings = $hash->to32BitStrings();
echo "\n";
foreach ($strings as $string) {
  echo "$string\n";
}

$strings = $hash->to64BitStrings();
echo "\n";
foreach ($strings as $string) {
  echo "$string\n";
}

