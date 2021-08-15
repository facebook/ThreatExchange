# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

output "pdq_hasher_function_name" {
  value = aws_lambda_function.pdq_hasher.function_name
}

output "pdq_matcher_function_name" {
  value = aws_lambda_function.pdq_matcher.function_name
}

output "hashes_queue_name" {
  value = aws_sqs_queue.hashes_queue.name
}

output "hashes_queue_url" {
  value = aws_sqs_queue.hashes_queue.id
}
