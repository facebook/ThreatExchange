<?php

// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

// ================================================================
// This file is bottom-up: more detailed methods at the top, main
// entry points at the bottom. Namely:
//
// * computeHashAndQualityFromFilename:
//   Returns an array of PDQHash object and integer 0-100 quality.
//
// * computeHashesAndQualityFromFilename:
//   Returns an array of [array of eight PDQHash objects keyed by rotation/flip
//   name] and integer 0-100 quality.
//
// These first two are pure-PHP. The downsample phase is the most expensive
// part of PDQ, so these use the GD library to downsample first.
//
// * computeStringHashAndQualityFromFilenameUsingExtension:
//   Returns an array of hex-string hash and integer 0-100 quality.
//
// * computeStringHashesAndQualityFromFilenameUsingExtension
//   Returns array of [array of eight hex-string hashes keyed by rotation/flip
//   name] and integer 0-100 quality.
//
// These last two use a C-language Zend extension to do most of the work.
// ================================================================

require 'pdqhash.php';

class PDQHasher {
    const LUMA_FROM_R_COEFF = 0.299;
    const LUMA_FROM_G_COEFF = 0.587;
    const LUMA_FROM_B_COEFF = 0.114;

    const PDQ_JAROSZ_WINDOW_SIZE_DIVISOR = 128;
    const PDQ_NUM_JAROSZ_XY_PASSES = 2;

    // Hashes for various dihedral transformations of the image.
    // Note, you can also transform the image and hash that.
    const DIH_ORIGINAL     = 0x01;
    const DIH_ROTATE_90    = 0x02;
    const DIH_ROTATE_180   = 0x04;
    const DIH_ROTATE_270   = 0x08;
    const DIH_FLIP_X       = 0x10;
    const DIH_FLIP_Y       = 0x20;
    const DIH_FLIP_PLUS_1  = 0x40;
    const DIH_FLIP_MINUS_1 = 0x80;
    const DIH_ALL          = 0xff;

  // ----------------------------------------------------------------
  // Handles greyscale or RGB.
  //
  // It's not obvious (to me) which is which: for JPEG the channel count is
  // available from getimagesize() while for PNG it isn't.
  //
  // But it doesn't matter due to how PHP handles pixels: for RGB the triples
  // are OR'ed into a 24-bit value while for greyscale they're the lower 8
  // bits. So we get greyscale as 'blue', multiplied by an arbitrary scaling
  // coefficient which doesn't affect the median property of the DCT output.

  static function imageToLumaMatrix(
    $image, // resource
    $num_rows,
    $num_cols
  ) {
    $luma_matrix = array();
    for ($i = 0; $i < $num_rows; $i++) {
      $row = array();
      for ($j = 0; $j < $num_cols; $j++) {
        $pixel = imagecolorat($image, $j, $i);
        $r = $pixel >> 16;
        $g = ($pixel >> 8) & 0xff;
        $b = $pixel & 0xff;
        $y = self::LUMA_FROM_R_COEFF * $r
           + self::LUMA_FROM_G_COEFF * $g
           + self::LUMA_FROM_B_COEFF * $b;
        $row[$j] = $y;
      }
      $luma_matrix[$i] = $row;
    }
    return $luma_matrix;
  }

  // ================================================================
  // Wojciech Jarosz 'Fast Image Convolutions' ACM SIGGRAPH 2001:
  // X,Y,X,Y passes of 1-D box filters produces a 2D tent filter.
  //
  // Since PDQ uses 64x64 blocks, 1/64th of the image height/width respectively is
  // a full block. But since we use two passes, we want half that window size per
  // pass. Example: 1024x1024 full-resolution input. PDQ downsamples to 64x64.
  // Each 16x16 block of the input produces a single downsample pixel.  X,Y passes
  // with window size 8 (= 1024/128) average pixels with 8x8 neighbors. The second
  // X,Y pair of 1D box-filter passes accumulate data from all 16x16.

  // ----------------------------------------------------------------
  static function computeJaroszFilterWindowSize(
    $dimension
  ) {

    return (int)(($dimension + self::PDQ_JAROSZ_WINDOW_SIZE_DIVISOR - 1)
      / self::PDQ_JAROSZ_WINDOW_SIZE_DIVISOR);
  }

  // ----------------------------------------------------------------
  // 7 and 4
  //
  //    0 0 0 0 0 0 0 0 0 0 1 1 1 1 1 1
  //    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5
  //
  //    .                                PHASE 1: ONLY ADD, NO WRITE, NO SUBTRACT
  //    . .
  //    . . .
  //
  //  0 * . . .                          PHASE 2: ADD, WRITE, WITH NO SUBTRACTS
  //  1 . * . . .
  //  2 . . * . . .
  //  3 . . . * . . .
  //
  //  4   . . . * . . .                  PHASE 3: WRITES WITH ADD & SUBTRACT
  //  5     . . . * . . .
  //  6       . . . * . . .
  //  7         . . . * . . .
  //  8           . . . * . . .
  //  9             . . . * . . .
  // 10               . . . * . . .
  // 11                 . . . * . . .
  // 12                   . . . * . . .
  //
  // 13                     . . . * . .  PHASE 4: FINAL WRITES WITH NO ADDS
  // 14                       . . . * .
  // 15                         . . . *
  //
  //         = 0                                     =  0   PHASE 1
  //         = 0+1                                   =  1
  //         = 0+1+2                                 =  3
  //
  // out[ 0] = 0+1+2+3                               =  6   PHASE 2
  // out[ 1] = 0+1+2+3+4                             = 10
  // out[ 2] = 0+1+2+3+4+5                           = 15
  // out[ 3] = 0+1+2+3+4+5+6                         = 21
  //
  // out[ 4] =   1+2+3+4+5+6+7                       = 28   PHASE 3
  // out[ 5] =     2+3+4+5+6+7+8                     = 35
  // out[ 6] =       3+4+5+6+7+8+9                   = 42
  // out[ 7] =         4+5+6+7+8+9+10                = 49
  // out[ 8] =           5+6+7+8+9+10+11             = 56
  // out[ 9] =             6+7+8+9+10+11+12          = 63
  // out[10] =               7+8+9+10+11+12+13       = 70
  // out[11] =                 8+9+10+11+12+13+14    = 77
  // out[12] =                   9+10+11+12+13+14+15 = 84
  //
  // out[13] =                     10+11+12+13+14+15 = 75  PHASE 4
  // out[14] =                        11+12+13+14+15 = 65
  // out[15] =                           12+13+14+15 = 54
  // ----------------------------------------------------------------

  // ----------------------------------------------------------------
  // 8 and 5
  //
  //    0 0 0 0 0 0 0 0 0 0 1 1 1 1 1 1
  //    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5
  //
  //    .                                PHASE 1: ONLY ADD, NO WRITE, NO SUBTRACT
  //    . .
  //    . . .
  //    . . . .
  //
  //  0 * . . . .                        PHASE 2: ADD, WRITE, WITH NO SUBTRACTS
  //  1 . * . . . .
  //  2 . . * . . . .
  //  3 . . . * . . . .
  //
  //  4   . . . * . . . .                PHASE 3: WRITES WITH ADD & SUBTRACT
  //  5     . . . * . . . .
  //  6       . . . * . . . .
  //  7         . . . * . . . .
  //  8           . . . * . . . .
  //  9             . . . * . . . .
  // 10               . . . * . . . .
  // 11                 . . . * . . . .
  //
  // 12                   . . . * . . .  PHASE 4: FINAL WRITES WITH NO ADDS
  // 13                     . . . * . .
  // 14                       . . . * .
  // 15                         . . . *
  //
  //         = 0                                     =  0   PHASE 1
  //         = 0+1                                   =  1
  //         = 0+1+2                                 =  3
  //         = 0+1+2+3                               =  6
  //
  // out[ 0] = 0+1+2+3+4                             = 10
  // out[ 1] = 0+1+2+3+4+5                           = 15
  // out[ 2] = 0+1+2+3+4+5+6                         = 21
  // out[ 3] = 0+1+2+3+4+5+6+7                       = 28
  //
  // out[ 4] =   1+2+3+4+5+6+7+8                     = 36   PHASE 3
  // out[ 5] =     2+3+4+5+6+7+8+9                   = 44
  // out[ 6] =       3+4+5+6+7+8+9+10                = 52
  // out[ 7] =         4+5+6+7+8+9+10+11             = 60
  // out[ 8] =           5+6+7+8+9+10+11+12          = 68
  // out[ 9] =             6+7+8+9+10+11+12+13       = 76
  // out[10] =               7+8+9+10+11+12+13+14    = 84
  // out[11] =                 8+9+10+11+12+13+14+15 = 92
  //
  // out[12] =                   9+10+11+12+13+14+15 = 84  PHASE 4
  // out[13] =                     10+11+12+13+14+15 = 75  PHASE 4
  // out[14] =                        11+12+13+14+15 = 65
  // out[15] =                           12+13+14+15 = 54
  // ----------------------------------------------------------------

  // ----------------------------------------------------------------
  static function boxAlongCols(
    &$in_image, // 2D array of float
    &$out_image, // 2D array of float
    $num_rows,
    $num_cols,
    $window_size
  ) {
    for ($j = 0; $j < $num_cols; $j++) {
      $half_window_size = (int)(($window_size + 2) / 2); // 7->4, 8->5

      $phase_1_nreps = $half_window_size - 1;
      $phase_2_nreps = $window_size - $half_window_size + 1;
      $phase_3_nreps = $num_rows - $window_size;
      $phase_4_nreps = $half_window_size - 1;

      $li = 0; // Index of left edge of read window, for subtracts
      $ri = 0; // Index of right edge of read windows, for adds
      $oi = 0; // Index into output vector

      $sum = 0.0;
      $current_window_size = 0;

      // PHASE 1: ACCUMULATE FIRST SUM NO WRITES
      for ($k = 0; $k < $phase_1_nreps; $k++) {
        $sum += $in_image[$ri][$j];
        $current_window_size++;
        $ri++;
      }

      // PHASE 2: INITIAL WRITES WITH SMALL WINDOW
      for ($k = 0; $k < $phase_2_nreps; $k++) {
        $sum += $in_image[$ri][$j];
        $current_window_size++;
        $out_image[$oi][$j] = $sum / $current_window_size;
        $ri++;
        $oi++;
      }

      // PHASE 3: WRITES WITH FULL WINDOW
      for ($k = 0; $k < $phase_3_nreps; $k++) {
        $sum += $in_image[$ri][$j];
        $sum -= $in_image[$li][$j];
        $out_image[$oi][$j] = $sum / $current_window_size;
        $li++;
        $ri++;
        $oi++;
      }

      // PHASE 4: FINAL WRITES WITH SMALL WINDOW
      for ($k = 0; $k < $phase_4_nreps; $k++) {
        $sum -= $in_image[$li][$j];
        $current_window_size--;
        $out_image[$oi][$j] = $sum / $current_window_size;
        $li++;
        $oi++;
      }
    }
  }

  static function boxAlongRows(
    &$in_image, // 2D array of float
    &$out_image, // 2D array of float
    $num_rows,
    $num_cols,
    $window_size
  ) {
    for ($i = 0; $i < $num_rows; $i++) {
      $half_window_size = (int)(($window_size + 2) / 2); // 7->4, 8->5

      $phase_1_nreps = $half_window_size - 1;
      $phase_2_nreps = $window_size - $half_window_size + 1;
      $phase_3_nreps = $num_cols - $window_size;
      $phase_4_nreps = $half_window_size - 1;

      $li = 0; // Index of left edge of read window, for subtracts
      $ri = 0; // Index of right edge of read windows, for adds
      $oi = 0; // Index into output vector

      $sum = 0.0;
      $current_window_size = 0;

      // PHASE 1: ACCUMULATE FIRST SUM NO WRITES
      for ($k = 0; $k < $phase_1_nreps; $k++) {
        $sum += $in_image[$i][$ri];
        $current_window_size++;
        $ri++;
      }

      // PHASE 2: INITIAL WRITES WITH SMALL WINDOW
      for ($k = 0; $k < $phase_2_nreps; $k++) {
        $sum += $in_image[$i][$ri];
        $current_window_size++;
        $out_image[$i][$oi] = $sum / $current_window_size;
        $ri++;
        $oi++;
      }

      // PHASE 3: WRITES WITH FULL WINDOW
      for ($k = 0; $k < $phase_3_nreps; $k++) {
        $sum += $in_image[$i][$ri];
        $sum -= $in_image[$i][$li];
        $out_image[$i][$oi] = $sum / $current_window_size;
        $li++;
        $ri++;
        $oi++;
      }

      // PHASE 4: FINAL WRITES WITH SMALL WINDOW
      for ($k = 0; $k < $phase_4_nreps; $k++) {
        $sum -= $in_image[$i][$li];
        $current_window_size--;
        $out_image[$i][$oi] = $sum / $current_window_size;
        $li++;
        $oi++;
      }
    }
  }

  // ----------------------------------------------------------------
  static function jaroszFilter(
    &$luma_matrix, // 2D array of float
    $num_rows,
    $num_cols,
    $window_size_along_rows,
    $window_size_along_cols
  ) {

    $other_matrix = array();
    for ($i = 0; $i < $num_rows; $i++) {
      $row = array();
      for ($j = 0; $j < $num_cols; $j++) {
        $row[$j] = 0;
      }
      $other_matrix[$i] = $row;
    }

    for ($k = 0; $k < self::PDQ_NUM_JAROSZ_XY_PASSES; $k++) {
      self::boxAlongRows($luma_matrix, $other_matrix, $num_rows, $num_cols, $window_size_along_rows);
      self::boxAlongCols($other_matrix, $luma_matrix, $num_rows, $num_cols, $window_size_along_cols);
    }

  }

  // ================================================================
  // This is all heuristic (see the PDQ hashing doc). Quantization matters since
  // we want to count *significant* gradients, not just the some of many small
  // ones. The constants are all manually selected, and tuned as described in the
  // document.
  static function computeImageDomainQualityMetric(
    &$buffer_64x64
  ) {
    $int_gradient_sum = 0;

    for ($i = 0; $i < 63; $i++) {
      for ($j = 0; $j < 64; $j++) {
        $u = $buffer_64x64[$i][$j];
        $v = $buffer_64x64[$i+1][$j];
        $d = (int)((($u - $v) * 100) / 255);
        $int_gradient_sum += (int)abs($d);
      }
    }
    for ($i = 0; $i < 64; $i++) {
      for ($j = 0; $j < 63; $j++) {
        $u = $buffer_64x64[$i][$j];
        $v = $buffer_64x64[$i][$j+1];
        $d = (int)((($u - $v) * 100) / 255);
        $int_gradient_sum += (int)abs($d);
      }
    }

    // Heuristic scaling factor.
    $quality = (int)($int_gradient_sum / 90);
    if ($quality > 100) {
      $quality = 100;
    }

    return $quality;
  }

  // ================================================================
  // Full 64x64 to 64x64 can be optimized e.g. the Lee algorithm.  But here we
  // only want slots (1-16)x(1-16) of the full 64x64 output. Careful experiments
  // showed that using Lee along all 64 slots in one dimension, then Lee along 16
  // slots in the second, followed by extracting slots 1-16 of the output, was
  // actually slower than the current implementation which is completely
  // non-clever/non-Lee but computes only what is needed.

  static function computeDCT64To16(
    &$buffer_64x64,
    &$buffer_16x64,
    &$buffer_16x16,
    &$dct_16x64
  ) {
    // A = buffer_64x64
    // T = buffer_16x64
    // B = buffer_16x16
    // D = DCT matrix

    // 2D DCT:
    //   B = D A Dt
    // Split out into first product and second:
    //   B = (D A) Dt ; T = D A

    for ($i = 0; $i < 16; $i++) {
      for ($j = 0; $j < 64; $j++) {
        $sumk = 0.0;
        for ($k = 0; $k < 64; $k++) {
          $sumk += $dct_16x64[$i][$k] * $buffer_64x64[$k][$j];
        }
        $buffer_16x64[$i][$j] = $sumk;
      }
    }

    for ($i = 0; $i < 16; $i++) {
      for ($j = 0; $j < 16; $j++) {
        $sumk = 0.0;
          // sumk += T[i][k] * D[j][k];
        for ($k = 0; $k < 64; $k++) {
          $sumk += $buffer_16x64[$i][$k] * $dct_16x64[$j][$k];
        }
        $buffer_16x16[$i][$j] = $sumk;
      }
    }
  }

  // ----------------------------------------------------------------
  // orig      rot90     rot180    rot270
  // noxpose   xpose     noxpose   xpose
  // + + + +   - + - +   + - + -   - - - -
  // + + + +   - + - +   - + - +   + + + +
  // + + + +   - + - +   + - + -   - - - -
  // + + + +   - + - +   - + - +   + + + +
  //
  // flipx     flipy     flipplus  flipminus
  // noxpose   noxpose   xpose     xpose
  // - - - -   - + - +   + + + +   + - + -
  // + + + +   - + - +   + + + +   - + - +
  // - - - -   - + - +   + + + +   + - + -
  // + + + +   - + - +   + + + +   - + - +

  static function dct16OriginalToRotate90(&$A, &$B) {
    for ($i = 0; $i < 16; $i++) {
      for ($j = 0; $j < 16; $j++) {
        if ($j & 1) {
          $B[$j][$i] = $A[$i][$j];
        } else {
          $B[$j][$i] = -$A[$i][$j];
        }
      }
    }
  }

  static function dct16OriginalToRotate180(&$A, &$B) {
    for ($i = 0; $i < 16; $i++) {
      for ($j = 0; $j < 16; $j++) {
        if (($i+$j) & 1) {
          $B[$i][$j] = -$A[$i][$j];
        } else {
          $B[$i][$j] = $A[$i][$j];
        }
      }
    }
  }

  static function dct16OriginalToRotate270(&$A, &$B) {
    for ($i = 0; $i < 16; $i++) {
      for ($j = 0; $j < 16; $j++) {
        if ($i & 1) {
          $B[$j][$i] = $A[$i][$j];
        } else {
          $B[$j][$i] = -$A[$i][$j];
        }
      }
    }
  }

  static function dct16OriginalToFlipX(&$A, &$B) {
    for ($i = 0; $i < 16; $i++) {
      for ($j = 0; $j < 16; $j++) {
        if ($i & 1) {
          $B[$i][$j] = $A[$i][$j];
        } else {
          $B[$i][$j] = -$A[$i][$j];
        }
      }
    }
  }

  static function dct16OriginalToFlipY(&$A, &$B) {
    for ($i = 0; $i < 16; $i++) {
      for ($j = 0; $j < 16; $j++) {
        if ($j & 1) {
          $B[$i][$j] = $A[$i][$j];
        } else {
          $B[$i][$j] = -$A[$i][$j];
        }
      }
    }
  }

  static function dct16OriginalToFlipPlus1(&$A, &$B) {
    for ($i = 0; $i < 16; $i++) {
      for ($j = 0; $j < 16; $j++) {
        $B[$j][$i] = $A[$i][$j];
      }
    }
  }

  static function dct16OriginalToFlipMinus1(&$A, &$B) {
    for ($i = 0; $i < 16; $i++) {
      for ($j = 0; $j < 16; $j++) {
        if (($i+$j) & 1) {
          $B[$j][$i] = -$A[$i][$j];
        } else {
          $B[$j][$i] = $A[$i][$j];
        }
      }
    }
  }

  // ----------------------------------------------------------------
  static function computeHashFromDCTOutput(
    &$buffer_16x16
  ) {
    $flat_matrix = array();
    for ($k = 0, $i = 0; $i < 16; $i++) {
      for ($j = 0; $j < 16; $j++, $k++) {
        $flat_matrix[$k] = $buffer_16x16[$i][$j];
      }
    }

    sort($flat_matrix);
    //print_r($flat_matrix);

    $median = $flat_matrix[127];
    //echo "median=$median\n";

    $hash = PDQHash::makeZeroesHash();
    for ($k = 0, $i = 0; $i < 16; $i++) {
      for ($j = 0; $j < 16; $j++, $k++) {
        $value = $buffer_16x16[$i][$j];
        if ($value > $median) {
          $hash->setBit($k);
        }
      }
    }

    return $hash;
  }

  // ================================================================
  static function readImageFromFilename($filename, $downsample_first) {
    $is_jpeg = false;
    if (substr_compare($filename,'.jpg', -strlen('.jpg')) === 0) {
      $orig_image = imagecreatefromjpeg($filename);
      $is_jpeg = true;
    } else if (substr_compare($filename,'.jpeg', -strlen('.jpeg')) === 0) {
      $orig_image = imagecreatefromjpeg($filename);
      $is_jpeg = true;
    } else if (substr_compare($filename,'.png', -strlen('.png')) === 0) {
      $orig_image = imagecreatefrompng($filename);
    } else {
      throw new Exception('PDQHasher: could not handle filetype of '.$filename);
    }

    // The pure-PHP hasher is *really* slow in pure PHP for megapixel images.
    // So, downsample first. Don't worry about aspect ratio since PDQ will
    // squarify anyway. For extension use, don't downsample here as it's
    // redundant.
    if ($downsample_first) {
      $orig_height = imagesy($orig_image);
      $orig_width = imagesx($orig_image);
      if ($orig_height > 128 || $orig_width > 128) {
        $image = imagecreatetruecolor(128, 128);
        imagecopyresampled($image, $orig_image, 0, 0, 0, 0, 128, 128, $orig_width, $orig_height);
      } else {
        $image = $orig_image;
      }
    } else {
      $image = $orig_image;
    }

// NOTE: the PDQ hashes within ThreatExchange aren't respecting EXIF rotation tags
// so we should likewise ignore them.
//
//    if ($is_jpeg) {
//      $exif = exif_read_data($filename);
//      if (!empty($exif['Orientation'])) {
//        switch ($exif['Orientation']) {
//        case 3:
//          $image = imagerotate($image, 180, 0);
//          break;
//        case 6:
//          $image = imagerotate($image, -90, 0);
//          break;
//        case 8:
//          $image = imagerotate($image, 90, 0);
//          break;
//        }
//      }
//    }

    return $image;
  }

  // ================================================================
  static function computeDCTAndQualityFromImage(
    /*resource*/&$image,
    /*bool*/ $show_timings,
    /*bool*/ $dump
  ) {
    $num_rows = imagesy($image);
    $num_cols = imagesx($image);
    if ($dump) {
      echo "num_rows=$num_rows\n";
      echo "num_cols=$num_cols\n";
    }

    //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    // RGB to luma
    $t1 = microtime(true);
    $luma_matrix = self::imageToLumaMatrix($image, $num_rows, $num_cols);
    $t2 = microtime(true);
    if ($show_timings) {
      printf("X010-LUMA %.6f\n", $t2-$t1);
    }

    //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    // Downsample (blur and decimate)
    $t1 = microtime(true);
    $window_size_along_rows = self::computeJaroszFilterWindowSize($num_cols);
    $window_size_along_cols = self::computeJaroszFilterWindowSize($num_rows);
    self::jaroszFilter($luma_matrix, $num_rows, $num_cols, $window_size_along_rows, $window_size_along_cols);
    $t2 = microtime(true);
    if ($show_timings) {
      printf("X020-JRSZ %.6f\n", $t2-$t1);
    }

    // Decimation per se. Target centers not corners.
    $buffer_64x64 = array();
    for ($i = 0; $i < 64; $i++) {
      $row = array();
      for ($j = 0; $j < 64; $j++) {
        $row[$j] = 0;
      }
      $buffer_64x64[$i] = $row;
    }
    $t1 = microtime(true);
    for ($i = 0; $i < 64; $i++) {
      $ini = (int)((($i + 0.5) * $num_rows) / 64);
      for ($j = 0; $j < 64; $j++) {
        $inj = (int)((($j + 0.5) * $num_cols) / 64);
        $buffer_64x64[$i][$j] = $luma_matrix[$ini][$inj];
      }
    }
    $t2 = microtime(true);
    if ($dump) {
      echo "DOWNSAMPLE IMAGE:\n";
      print_r($buffer_64x64);
    }
    if ($show_timings) {
      printf("X030-DSMP %.6f\n", $t2-$t1);
    }

    //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    // Quality metric.  Reuse the 64x64 image-domain downsample
    // since we already have it.
    $t1 = microtime(true);
    $quality = self::computeImageDomainQualityMetric($buffer_64x64);
    $t2 = microtime(true);
    if ($show_timings) {
      printf("X040-QMTC %.6f\n", $t2-$t1);
    }
    if ($dump) {
      echo "QUALITY:$quality\n";
    }

    //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    $t1 = microtime(true);

    $buffer_16x64 = array();
    for ($i = 0; $i < 16; $i++) {
      $row = array();
      for ($j = 0; $j < 64; $j++) {
        $row[$j] = 0;
      }
      $buffer_16x64[$i] = $row;
    }

    $buffer_16x16 = array();
    for ($i = 0; $i < 16; $i++) {
      $row = array();
      for ($j = 0; $j < 16; $j++) {
        $row[$j] = 0;
      }
      $buffer_16x16[$i] = $row;
    }

    $dct_16x64 = array();
    for ($i = 0; $i < 16; $i++) {
      $row = array();
      for ($j = 0; $j < 64; $j++) {
        $row[$j] = 0;
      }
      $dct_16x64[$i] = $row;
    }
    // See comments on dct64To16. Input is (0..63)x(0..63); output is
    // (1..16)x(1..16) with the latter indexed as (0..15)x(0..15).
    $matrix_scale_factor = sqrt(2.0 / 64.0);
    $pi = 3.141592653589793;
    for ($i = 0; $i < 16; $i++) {
      for ($j = 0; $j < 64; $j++) {
        $dct_16x64[$i][$j] = $matrix_scale_factor *
          cos(($pi / 2 / 64.0) * ($i+1) * (2 * $j + 1));
      }
    }
    $t2 = microtime(true);
    if ($show_timings) {
      printf("X050-DMTX %.6f\n", $t2-$t1);
    }
    if ($dump) {
      echo "DCT MATRIX:\n";
      print_r($dct_16x64);
    }

    // 2D DCT
    $t1 = microtime(true);
    self::computeDCT64To16($buffer_64x64, $buffer_16x64, $buffer_16x16, $dct_16x64);
    $t2 = microtime(true);
    if ($show_timings) {
      printf("X060-CDCT %.6f\n", $t2-$t1);
    }
    if ($dump) {
      echo "DCT OUTPUT:\n";
      print_r($buffer_16x16);
    }

    return array($buffer_16x16, $quality);
  }

  // ----------------------------------------------------------------
  static function computeHashAndQualityFromImage(
    /*resource*/&$image,
    /*bool*/ $show_timings,
    /*bool*/ $dump
  ) {
    $t01 = microtime(true);

    //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    list ($buffer_16x16, $quality) = self:: computeDCTAndQualityFromImage(
      $image, $show_timings, $dump
    );

    //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    $hash = self::computeHashFromDCTOutput($buffer_16x16);
    if ($dump) {
      echo "HASH:".$hash->toHexString()."\n";
    }
    $t02 = microtime(true);
    if ($show_timings) {
      printf("X999-OVRL %.6f\n", $t02-$t01);
    }

    //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    return array($hash, $quality);
  }

  // ----------------------------------------------------------------
  static function computeHashesAndQualityFromImage(
    /*resource*/&$image,
    /*int*/ $which_flags = self::DIH_ALL,
    /*bool*/ $show_timings,
    /*bool*/ $dump
  ) {
    $t01 = microtime(true);

    //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    list ($buffer_16x16, $quality) = self:: computeDCTAndQualityFromImage(
      $image, $show_timings, $dump
    );

    $buffer_16x16_aux = array();
    for ($i = 0; $i < 16; $i++) {
      $row = array();
      for ($j = 0; $j < 16; $j++) {
        $row[$j] = 0;
      }
      $buffer_16x16_aux[$i] = $row;
    }

    //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    $hashes = array();

    if ($which_flags & self::DIH_ORIGINAL) {
      $hashes['orig'] = self::computeHashFromDCTOutput($buffer_16x16);
    }

    if ($which_flags & self::DIH_ROTATE_90) {
      self::dct16OriginalToRotate90($buffer_16x16, $buffer_16x16Aux);
      $hashes['r090'] = self::computeHashFromDCTOutput($buffer_16x16Aux);
    }

    if ($which_flags & self::DIH_ROTATE_180) {
      self::dct16OriginalToRotate180($buffer_16x16, $buffer_16x16Aux);
      $hashes['r180'] = self::computeHashFromDCTOutput($buffer_16x16Aux);
    }

    if ($which_flags & self::DIH_ROTATE_270) {
      self::dct16OriginalToRotate270($buffer_16x16, $buffer_16x16Aux);
      $hashes['r270'] = self::computeHashFromDCTOutput($buffer_16x16Aux);
    }

    if ($which_flags & self::DIH_FLIP_X) {
      self::dct16OriginalToFlipX($buffer_16x16, $buffer_16x16Aux);
      $hashes['flpx'] = self::computeHashFromDCTOutput($buffer_16x16Aux);
    }

    if ($which_flags & self::DIH_FLIP_Y) {
      self::dct16OriginalToFlipY($buffer_16x16, $buffer_16x16Aux);
      $hashes['flpy'] = self::computeHashFromDCTOutput($buffer_16x16Aux);
    }

    if ($which_flags & self::DIH_FLIP_PLUS_1) {
      self::dct16OriginalToFlipPlus1($buffer_16x16, $buffer_16x16Aux);
      $hashes['flpp'] = self::computeHashFromDCTOutput($buffer_16x16Aux);
    }

    if ($which_flags & self::DIH_FLIP_MINUS_1) {
      self::dct16OriginalToFlipMinus1($buffer_16x16, $buffer_16x16Aux);
      $hashes['flpm'] = self::computeHashFromDCTOutput($buffer_16x16Aux);
    }

    $t02 = microtime(true);
    if ($show_timings) {
      printf("X999-OVRL %.6f\n", $t02-$t01);
    }

    //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    return array($hashes, $quality);
  }

  // ================================================================
  static function computeHashAndQualityFromFilename(
    $filename,
    $show_timings = false,
    $dump = false,
    $downsample = false
  ) {

    $t01 = microtime(true);

    //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    $info = getimagesize($filename);
    if ($dump) {
      echo "IMAGE INFO:\n";
      print_r($info);
    }

    $num_rows = $info[1]; // height
    $num_cols = $info[0]; // width
    if ($dump) {
      echo "num_rows=$num_rows\n";
      echo "num_cols=$num_cols\n";
    }

    //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    $t1 = microtime(true);
    $image = self::readImageFromFilename($filename, $downsample);
    $t2 = microtime(true);
    if ($show_timings) {
      printf("X000-READ %.6f\n", $t2-$t1);
    }

    return self::computeHashAndQualityFromImage($image, $show_timings, $dump);
  }

  // ----------------------------------------------------------------
  static function computeHashesAndQualityFromFilename(
    $filename,
    $which_flags = self::DIH_ALL,
    $show_timings = false,
    $dump = false
  ) {

    $t01 = microtime(true);

    //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    $info = getimagesize($filename);
    if ($dump) {
      echo "IMAGE INFO:\n";
      print_r($info);
    }

    $num_rows = $info[1]; // height
    $num_cols = $info[0]; // width
    if ($dump) {
      echo "num_rows=$num_rows\n";
      echo "num_cols=$num_cols\n";
    }

    //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    $t1 = microtime(true);
    $image = self::readImageFromFilename($filename, true);
    $t2 = microtime(true);
    if ($show_timings) {
      printf("X000-READ %.6f\n", $t2-$t1);
    }

    return self::computeHashesAndQualityFromImage(
      $image, $which_flags, $show_timings, $dump
    );
  }

  // ================================================================
  // Array of hash and quality.
  // The hash is a hex-string, not a PDQHash object.

  static function computeStringHashAndQualityFromFilenameUsingExtension(
    $filename,
    $show_timings = false,
    $dump = false
  ) {

    $t01 = microtime(true);

    //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    $info = getimagesize($filename);
    if ($dump) {
      echo "IMAGE INFO:\n";
      print_r($info);
    }

    $num_rows = $info[1]; // height
    $num_cols = $info[0]; // width
    if ($dump) {
      echo "num_rows=$num_rows\n";
      echo "num_cols=$num_cols\n";
    }

    //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    $t1 = microtime(true);
    $image = self::readImageFromFilename($filename, false);
    $t2 = microtime(true);
    if ($show_timings) {
      printf("X000-READ %.6f\n", $t2-$t1);
    }

    // Uses the PDQ Zend-PHP extension
    $t1 = microtime(true);
    $retval = pdq_compute_string_hash_and_quality_from_image_resource($image);
    $t2 = microtime(true);
    if ($show_timings) {
      printf("X000-EXTN %.6f\n", $t2-$t1);
    }

    return array($retval['hash'], $retval['quality']);
  }

  // ----------------------------------------------------------------
  static function computeStringHashesAndQualityFromFilenameUsingExtension(
    $filename,
    $which_flags = self::DIH_ALL,
    $show_timings = false,
    $dump = false
  ) {

    $t01 = microtime(true);

    //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    $info = getimagesize($filename);
    if ($dump) {
      echo "IMAGE INFO:\n";
      print_r($info);
    }

    $num_rows = $info[1]; // height
    $num_cols = $info[0]; // width
    if ($dump) {
      echo "num_rows=$num_rows\n";
      echo "num_cols=$num_cols\n";
    }

    //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    $t1 = microtime(true);
    $image = self::readImageFromFilename($filename, false);
    $t2 = microtime(true);
    if ($show_timings) {
      printf("X000-READ %.6f\n", $t2-$t1);
    }

    // Uses the PDQ Zend-PHP extension
    $t1 = microtime(true);
    $retval = pdq_compute_string_hashes_and_quality_from_image_resource($image);
    $t2 = microtime(true);
    if ($show_timings) {
      printf("X000-EXTN %.6f\n", $t2-$t1);
    }

    return array(
      array(
        'orig' => $retval['orig'],
        'r090' => $retval['r090'],
        'r180' => $retval['r180'],
        'r270' => $retval['r270'],
        'flpx' => $retval['flpx'],
        'flpy' => $retval['flpy'],
        'flpp' => $retval['flpp'],
        'flpm' => $retval['flpm'],
      ),
      $retval['quality']
    );
  }

} // class PDQHasher
