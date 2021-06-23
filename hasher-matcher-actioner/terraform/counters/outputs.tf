# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

output "match_counter_function_name" {
  value = aws_lambda_function.match_counter.function_name
}

output "match_counter_queue_name" {
  value = aws_sqs_queue.match_counter_queue.name
}
