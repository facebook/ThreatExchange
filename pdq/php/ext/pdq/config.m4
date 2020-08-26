dnl
dnl $Id$
dnl

PHP_ARG_ENABLE(pdq, whether to enable PDQ image-hashing support,
[  --enable-pdq           Enable PDQ image-hashing support])

if test "$PHP_PDQ" = "yes"; then
  AC_DEFINE(HAVE_PDQ, 1, [Whether you want PDQ image-hashing support])
  extra_sources="impl/torben.c impl/pdqhashtypes.c impl/pdqhashing.c"
  PHP_NEW_EXTENSION(pdq, pdq.c $extra_sources, $ext_shared,, -DZEND_ENABLE_STATIC_TSRMLS_CACHE=1)
fi
