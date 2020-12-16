# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

output "lambda_arn" {
  value = aws_lambda_function.pdq_hasher_lambda.arn
}

output "input_queue_arn" {
  value = aws_sqs_queue.pdq_hasher_new_file_queue.arn
}

output "input_queue_id" {
  value = aws_sqs_queue.pdq_hasher_new_file_queue.id
}

output "output_topic_arn" {
  value = aws_sns_topic.pdq_hashes.arn
}
