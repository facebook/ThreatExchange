# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

output "invoke_url" {
  value = aws_apigatewayv2_stage.hma_apigateway.invoke_url
}

output "api_root_function_name" {
  value = aws_lambda_function.api_root.function_name
}

output "api_gateway_id" {
  value = aws_apigatewayv2_api.hma_apigateway.id
}
