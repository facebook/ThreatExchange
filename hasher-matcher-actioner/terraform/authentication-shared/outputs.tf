# Copyright (c) Meta Platforms, Inc. and affiliates.

output "webapp_and_api_shared_user_pool_id" {
  value = aws_cognito_user_pool.webapp_and_api_shared_user_pool.id
}

output "webapp_and_api_shared_user_pool_client_id" {
  value = aws_cognito_user_pool_client.webapp_and_api_shared_user_pool_client.id
}
