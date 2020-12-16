# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

output "lambda_arn" {
  value = aws_lambda_function.pdq_matcher_lambda.arn
}

output "input_queue_arn" {
  value = aws_sqs_queue.pdq_matcher_new_hash_queue.arn
}

output "input_queue_id" {
  value = aws_sqs_queue.pdq_matcher_new_hash_queue.id
}

output "output_topic_arn" {
  value = aws_sns_topic.pdq_matches.arn
}
