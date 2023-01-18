# Copyright (c) Meta Platforms, Inc. and affiliates.

output "webapp_and_api_user_pool_id" {
  value = var.use_shared_user_pool ? var.webapp_and_api_shared_user_pool_id : aws_cognito_user_pool.webapp_and_api_user_pool[0].id
}

output "webapp_and_api_user_pool_name" {
  # See terraform/authentication-shared/main.tf 
  value = var.use_shared_user_pool ? "shared-hma-user-pool" : aws_cognito_user_pool.webapp_and_api_user_pool[0].name
}

output "webapp_and_api_user_pool_client_id" {
  value = var.use_shared_user_pool ? var.webapp_and_api_shared_user_pool_client_id : aws_cognito_user_pool_client.webapp_and_api_user_pool_client[0].id
}
