// Copyright (c) Meta Platforms, Inc. and affiliates.
#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

// ================================================================
// INCLUDES

// PHP per se
#include "php.h"
#include "php_ini.h"

// The API we export
#include "php_pdq.h"

// Use the GD library, since we take GD image resources as input
#include "ext/gd/php_gd.h"
#include "ext/gd/libgd/gd.h"

// PDQ (PHP-independent) implementation
#include "impl/pdqhashing.h"

// ================================================================
// DEFINITION OF EXPORTED USERLAND FUNCTIONS

// Returns array with keys 'hash' and 'quality'
ZEND_BEGIN_ARG_INFO(arginfo_pdq_compute_string_hash_and_quality_from_image_resource, 0)
	ZEND_ARG_INFO(0, pgdImage) // resource
ZEND_END_ARG_INFO()
// xxx comment
ZEND_BEGIN_ARG_INFO(arginfo_pdq_compute_string_hashes_and_quality_from_image_resource, 0)
	ZEND_ARG_INFO(0, pgdImage) // resource
ZEND_END_ARG_INFO()

static zend_function_entry pdq_functions[] = {
	PHP_FE(pdq_compute_string_hash_and_quality_from_image_resource,
		arginfo_pdq_compute_string_hash_and_quality_from_image_resource)
	PHP_FE(pdq_compute_string_hashes_and_quality_from_image_resource,
		arginfo_pdq_compute_string_hashes_and_quality_from_image_resource)
	{NULL, NULL, NULL}
};

// ================================================================
// MODULE DEFINITION WE EXPORT

zend_module_entry pdq_module_entry = {
#if ZEND_MODULE_API_NO >= 20010901
	STANDARD_MODULE_HEADER,
#endif
	PHP_PDQ_EXTNAME,
	pdq_functions,
	NULL,
	NULL,
	NULL,
	NULL,
	NULL,
#if ZEND_MODULE_API_NO >= 20010901
	PHP_PDQ_VERSION,
#endif
	STANDARD_MODULE_PROPERTIES
};

#ifdef COMPILE_DL_PDQ
ZEND_GET_MODULE(pdq)
#endif

// ================================================================
// IMPLEMENTATION OF USERLAND FUNCTIONS

PHP_FUNCTION(pdq_compute_string_hash_and_quality_from_image_resource)
{
	zval *pzImage;
	gdImagePtr pgdImage;

	//  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	// There should be one argument: a GD image resource
	if (zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "r", &pzImage) == FAILURE) {
		return;
	}

#if PHP_MAJOR_VERSION == 5
	ZEND_FETCH_RESOURCE(pgdImage, gdImagePtr, &pzImage, -1, "Image", phpi_get_le_gd());
#else
	pgdImage = (gdImagePtr)zend_fetch_resource(Z_RES_P(pzImage), "Image", phpi_get_le_gd());
	if (pgdImage == NULL) {
		RETURN_FALSE;
	}
#endif

	//  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	// Convert the GD image buffer to a floating-point luminance matrix
	int num_rows = pgdImage->sy;
	int num_cols = pgdImage->sx;

	// Matrices in row-major order
	float *buffer1 = emalloc(sizeof(float) * num_rows * num_cols);
	float *buffer2 = emalloc(sizeof(float) * num_rows * num_cols);

	if (gdImageTrueColor(pgdImage)) {
		for (int i = 0; i < num_rows; i++) {
			for (int j = 0; j < num_cols; j++) {
				int pixel = gdImageTrueColorPixel(pgdImage, j, i);
				int r = (pixel >> 16) & 0xff;
				int g = (pixel >>  8) & 0xff;
				int b =  pixel        & 0xff;
				buffer1[i*num_cols+j] =
					luma_from_R_coeff * r +
					luma_from_G_coeff * g +
					luma_from_B_coeff * b;
			}
		}
	} else {
		for (int i = 0; i < num_rows; i++) {
			for (int j = 0; j < num_cols; j++) {
				int pixel = pgdImage->pixels[i][j];
				int r = (pixel >> 16) & 0xff;
				int g = (pixel >>  8) & 0xff;
				int b =  pixel        & 0xff;
				buffer1[i*num_cols+j] =
					luma_from_R_coeff * r +
					luma_from_G_coeff * g +
					luma_from_B_coeff * b;
			}
		}
	}

	//  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	// Call into the PDQ implementation

	// Outputs:
	Hash256 hash;
	int quality;

	// Work buffers:
	float buffer64x64[64][64];
	float buffer16x64[16][64];
	float buffer16x16[16][16];

	pdqHash256FromFloatLuma(
		buffer1,
		buffer2,
		num_rows,
		num_cols,
		buffer64x64,
		buffer16x64,
		buffer16x16,
		&hash,
		&quality);

	efree(buffer1);
	efree(buffer2);

	//  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	// Format the hash as string
	char *str = emalloc(HASH256_TEXT_LENGTH);
	Hash256Format(&hash, str);

	array_init(return_value);
#if PHP_MAJOR_VERSION == 5
	add_assoc_string(return_value, "hash", str, 1);
#else
	add_assoc_string(return_value, "hash", str);
#endif
	add_assoc_long(return_value, "quality", quality);
}

// ----------------------------------------------------------------
PHP_FUNCTION(pdq_compute_string_hashes_and_quality_from_image_resource)
{
	zval *pzImage;
	gdImagePtr pgdImage;

	//  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	// There should be one argument: a GD image resource
	if (zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "r", &pzImage) == FAILURE) {
		return;
	}

#if PHP_MAJOR_VERSION == 5
	ZEND_FETCH_RESOURCE(pgdImage, gdImagePtr, &pzImage, -1, "Image", phpi_get_le_gd());
#else
	pgdImage = (gdImagePtr)zend_fetch_resource(Z_RES_P(pzImage), "Image", phpi_get_le_gd());
	if (pgdImage == NULL) {
		RETURN_FALSE;
	}
#endif

	//  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	// Convert the GD image buffer to a floating-point luminance matrix
	int num_rows = pgdImage->sy;
	int num_cols = pgdImage->sx;

	// Matrices in row-major order
	float *buffer1 = emalloc(sizeof(float) * num_rows * num_cols);
	float *buffer2 = emalloc(sizeof(float) * num_rows * num_cols);

	if (gdImageTrueColor(pgdImage)) {
		for (int i = 0; i < num_rows; i++) {
			for (int j = 0; j < num_cols; j++) {
				int pixel = gdImageTrueColorPixel(pgdImage, j, i);
				int r = (pixel >> 16) & 0xff;
				int g = (pixel >>  8) & 0xff;
				int b =  pixel        & 0xff;
				buffer1[i*num_cols+j] =
					luma_from_R_coeff * r +
					luma_from_G_coeff * g +
					luma_from_B_coeff * b;
			}
		}
	} else {
		for (int i = 0; i < num_rows; i++) {
			for (int j = 0; j < num_cols; j++) {
				int pixel = pgdImage->pixels[i][j];
				int r = (pixel >> 16) & 0xff;
				int g = (pixel >>  8) & 0xff;
				int b =  pixel        & 0xff;
				buffer1[i*num_cols+j] =
					luma_from_R_coeff * r +
					luma_from_G_coeff * g +
					luma_from_B_coeff * b;
			}
		}
	}

	//  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	// Call into the PDQ implementation

	// Outputs:
	Hash256 hash_orig;
	Hash256 hash_r090;
	Hash256 hash_r180;
	Hash256 hash_r270;
	Hash256 hash_flpx;
	Hash256 hash_flpy;
	Hash256 hash_flpp;
	Hash256 hash_flpm;
	int quality;

	// Work buffers:
	float buffer64x64[64][64];
	float buffer16x64[16][64];
	float buffer16x16[16][16];
	float buffer16x16Aux[16][16];

	pdqDihedralHash256esFromFloatLuma(
		buffer1,
		buffer2,
		num_rows,
		num_cols,
		buffer64x64,
		buffer16x64,
		buffer16x16,
		buffer16x16Aux,
		&hash_orig,
		&hash_r090,
		&hash_r180,
		&hash_r270,
		&hash_flpx,
		&hash_flpy,
		&hash_flpp,
		&hash_flpm,
		&quality);

	efree(buffer1);
	efree(buffer2);

	//  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	// Format the hash as string
	char *str_orig = emalloc(HASH256_TEXT_LENGTH);
	char *str_r090 = emalloc(HASH256_TEXT_LENGTH);
	char *str_r180 = emalloc(HASH256_TEXT_LENGTH);
	char *str_r270 = emalloc(HASH256_TEXT_LENGTH);
	char *str_flpx = emalloc(HASH256_TEXT_LENGTH);
	char *str_flpy = emalloc(HASH256_TEXT_LENGTH);
	char *str_flpp = emalloc(HASH256_TEXT_LENGTH);
	char *str_flpm = emalloc(HASH256_TEXT_LENGTH);

	Hash256Format(&hash_orig, str_orig);
	Hash256Format(&hash_r090, str_r090);
	Hash256Format(&hash_r180, str_r180);
	Hash256Format(&hash_r270, str_r270);
	Hash256Format(&hash_flpx, str_flpx);
	Hash256Format(&hash_flpy, str_flpy);
	Hash256Format(&hash_flpp, str_flpp);
	Hash256Format(&hash_flpm, str_flpm);

	array_init(return_value);
#if PHP_MAJOR_VERSION == 5
	add_assoc_string(return_value, "orig", str_orig, 1);
	add_assoc_string(return_value, "r090", str_r090, 1);
	add_assoc_string(return_value, "r180", str_r180, 1);
	add_assoc_string(return_value, "r270", str_r270, 1);
	add_assoc_string(return_value, "flpx", str_flpx, 1);
	add_assoc_string(return_value, "flpy", str_flpy, 1);
	add_assoc_string(return_value, "flpp", str_flpp, 1);
	add_assoc_string(return_value, "flpm", str_flpm, 1);
#else
	add_assoc_string(return_value, "orig", str_orig);
	add_assoc_string(return_value, "r090", str_r090);
	add_assoc_string(return_value, "r180", str_r180);
	add_assoc_string(return_value, "r270", str_r270);
	add_assoc_string(return_value, "flpx", str_flpx);
	add_assoc_string(return_value, "flpy", str_flpy);
	add_assoc_string(return_value, "flpp", str_flpp);
	add_assoc_string(return_value, "flpm", str_flpm);
#endif
	add_assoc_long(return_value, "quality", quality);
}
