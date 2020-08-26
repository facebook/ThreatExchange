// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

#ifndef PHP_PDQ_H
#define PHP_PDQ_H

#define PHP_PDQ_VERSION "1.0"
#define PHP_PDQ_EXTNAME "pdq"

PHP_FUNCTION(pdq_compute_string_hash_and_quality_from_image_resource);
PHP_FUNCTION(pdq_compute_string_hashes_and_quality_from_image_resource);

extern zend_module_entry pdq_module_entry;
#define phpext_pdq_ptr &pdq_module_entry

#endif // PHP_PDQ_H
