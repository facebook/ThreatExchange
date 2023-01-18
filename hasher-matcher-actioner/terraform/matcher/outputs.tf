# Copyright (c) Meta Platforms, Inc. and affiliates.

output "matcher_function_name" {
  value = aws_lambda_function.matcher_lambda.function_name
}
