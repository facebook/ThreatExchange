# Copyright (c) Meta Platforms, Inc. and affiliates.

output "hasher_function_name" {
  value = aws_lambda_function.hashing_lambda.function_name
}
