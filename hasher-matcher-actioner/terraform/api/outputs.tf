# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

output "invoke_url" {
  value = "${aws_api_gateway_stage.hma_api_gw.invoke_url}/"
}

output "api_root_function_name" {
  value = aws_lambda_function.api_root.function_name
}

output "api_auth_function_name" {
  value = aws_lambda_function.api_auth.function_name
}

output "api_gateway_id" {
  value = aws_api_gateway_rest_api.hma_api_gw.id
}
