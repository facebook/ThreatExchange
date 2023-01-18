# Copyright (c) Meta Platforms, Inc. and affiliates.

# These root outputs can be used as inputs for tests of deployed instances.

# Overly general names for now as we mostly use the same s3 bucket/db for everything.
output "bucket_name" {
  value = module.hashing_data.image_folder_info.bucket_name
}
output "datastore_name" {
  value = module.datastore.primary_datastore.name
}
output "te_data_folder" {
  value = local.te_data_folder
}
output "prefix" {
  value = var.prefix
}
output "api_url" {
  value = module.api.invoke_url
}
output "cognito_user_pool_id" {
  value = module.authentication.webapp_and_api_user_pool_id
}
output "cognito_user_pool_name" {
  value = module.authentication.webapp_and_api_user_pool_name
}
output "cognito_user_pool_client_id" {
  value = module.authentication.webapp_and_api_user_pool_client_id
}

output "ui_url" {
  value = var.include_cloudfront_distribution ? module.webapp.cloudfront_distribution_domain_name : module.webapp.ui_url
}

output "submit_topic_arn" {
  value = var.create_submit_event_sns_topic_and_handler ? module.submit_events[0].submit_topic_arn : ""
}
output "action_performer_iam_role_arn" {
  value = module.actions.action_performer_iam_role_arn
}
