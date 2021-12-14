
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

output "indexer_function_name" {
  value = aws_lambda_function.indexer.function_name
}
output "indexer_function_arn" {
  value = aws_lambda_function.indexer.arn
}
