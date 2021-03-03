# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

# These root outputs can be used as inputs for tests of deployed instances.

# Overly general names for now as we use the same s3 bucket/db for everything.
output "bucket_name" {
  value = module.hashing_data.image_folder_info.bucket_name
}
output "datastore_name" {
  value = module.hashing_data.hma_datastore.name
}
output "prefix" {
  value = var.prefix
}

