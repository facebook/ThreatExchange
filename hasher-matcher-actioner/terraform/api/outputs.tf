# Copyright (c) Meta Platforms, Inc. and affiliates.

# the format of the invoke_url changes if we are using a private API
output "invoke_url" {
  value = var.api_in_vpc ? "https://${aws_api_gateway_rest_api.hma_api_gw.id}-${aws_vpc_endpoint.vpce[0].id}.execute-api.${data.aws_region.current.name}.amazonaws.com/${aws_api_gateway_stage.hma_api_gw.stage_name}/" : "${aws_api_gateway_stage.hma_api_gw.invoke_url}/"
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
