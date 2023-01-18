# Copyright (c) Meta Platforms, Inc. and affiliates.

output "submit_topic_arn" {
  value = aws_sns_topic.submit_event_notification_topic.arn
}

output "submit_event_handler_function_name" {
  value = aws_lambda_function.submit_event_handler.function_name
}

output "submit_event_queue_name" {
  value = aws_sqs_queue.submit_event_queue.name
}

output "submit_event_dlq_name" {
  value = aws_sqs_queue.submit_event_queue_dlq.name
}
