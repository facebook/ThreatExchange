# PDQ reference implementation: PHP

## Status

As of 2017-11-08 this is still preliminary. The image-hasher is coded in PHP
(pure-PHP as well as an optimized Zend extension in C); the index/search logic
(MIH, for mutually indexed hashing) is not. Likewise, the ops tools
(`hashtool256`, `clusterize256`, etc.) are all in the C++ version.

## Usage example

```
$ cat php.ini
memory_limit = -1;
include_path = ".";
extension=ext/pdq/modules/pdq.so;

$ php -c . pdqhashertest.php b.jpg
d8f8f0cec0f4a84f0637022a278f67f0b36e2ed596621e1d33e6339c4e9c9b22,100,purephp,b.jpg
d8f8f0cec0f4a84f0637022a278f67f0b36e2ed596621e1d33e6339c4e9c9b22,100,extnphp,b.jpg
```

## Early results

* Pure-PHP on a Macbook Air, 1600x1000 test image, 3.6 seconds.
* Pure-PHP, same hardware and image, using libgd calls to downsample first, 0.05 seconds. (This is because the most time-consuming part of PDQ is the downsample on a matrix of pixels, and using PHP arrays to index the `i,j` coordinates is inefficient.)
* Extension-PHP (C code), comparable amount of time.
* The extension-PHP version produces hashes with fewer bit-differences with respect to the C++ implementation (due to floating-point-rounding semantics in PHP vs. C++).

## To do

* Handle EXIF rotation tags found within JPEG images. Or not. The C++ implementation does not, so this should also not.

* Regression tests.

## Source code

As of 2017-11-08:

* `pdqhashertest.php`: Command-line entry point for hashing image files from the command line.
* `pdqhasherdihtest.php`: Same, but computes transformed hashes (rotations/flips) as well as the originals.
* `pdqhash.php`: The `PDQHash` class (256-bit vector with Hamming metric and hex I/O).
* `pdqhasher.php`: The PDQ hashing algorithm.
* `pdqhashtest.php`: Regression material for some implementation methods.

## Zend extension

Using pure PHP you get the
`PDQHasher::computeHashAndQualityFromFilename` and
`PDQHasher::computeHashesAndQualityFromFilename` methods. After the build steps here you can also call the
`PDQHasher::computeStringHashAndQualityFromFilenameUsingExtension` and
`PDQHasher::computeStringHashesAndQualityFromFilenameUsingExtension` methods.

* Have Zend-PHP installed on your system.
* Within `ext/pdq`, run `phpize`, then `./configure --enable-pdq` and `make`.
* This creates `ext/pdq/modules/pdq.so` which you can put in your installation's modules directory. Or, for local test, simply put `extension=ext/pdq/modules/pdq.so;` in your `php.ini`
* `php -c . pdqhashertest.php foo.jpg`

## Aside: building PHP7

This is not at all PDQ-specific, but it took me an hour or so of googling and
experimenting to get a PHP7 build with GD enabled. So, I thought I'd write up these
notes as a timesaver, in case anyone else finds them helpful. You need this only if you
want to build PHP7 from scratch. If your system already has PHP7, then the `phpize` etc.
stuff above should suffice.

Test if you have GD support in your system's PHP:
```
php -r "var_dump(function_exists('imagecreatefromjpeg'));"
bool(true) <--- then you are fine
-- or --
bool(false) <--- then PDQ won't work since it needs GD as a dependency
```

Obtain `php-7.1.11.tar.gz` from `php.net`, and unpack:
```
$ tar zvxf php-7.1.11.tar.gz
$ cd php-7.1.11
```

Search the local filesystem for `jpeglib.h`, `png.h`, and `zlib.h`. In my case I found:
```
/usr/local/opt/jpeg/include/jpeglib.h
/usr/local/opt/libpng/include/png.h
/usr/include/zlib.h
```

Configure to enable GD, and specify locations for dependent packages:
```
$ ./configure \
 --prefix=/usr/local/php7 \
 --with-gd \
 --with-jpeg-dir=/usr/local/opt/jpeg \
 --with-png-dir=/usr/local/opt/libpng \
 --with-zlib-dir=/usr

```

Build:
```
$ make
```

Check:
```
$ ./sapi/cli/php --version
PHP 7.1.11 (cli) (built: Nov 13 2017 21:07:21) ( NTS )
Copyright (c) 1997-2017 The PHP Group
Zend Engine v3.1.0, Copyright (c) 1998-2017 Zend Technologies

$ ./sapi/cli/php -r "var_dump(function_exists('imagecreatefromjpeg'));"
bool(true)
```

Install:
```
$ make install

$ /usr/local/php7/bin/php --version
PHP 7.1.11 (cli) (built: Nov 13 2017 21:07:21) ( NTS )
Copyright (c) 1997-2017 The PHP Group
Zend Engine v3.1.0, Copyright (c) 1998-2017 Zend Technologies
```

## Contact

threatexchange@meta.com
