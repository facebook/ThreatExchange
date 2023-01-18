
# Copyright (c) Meta Platforms, Inc. and affiliates.

output "indexer_function_name" {
  value = aws_lambda_function.indexer.function_name
}
output "indexer_function_arn" {
  value = aws_lambda_function.indexer.arn
}
