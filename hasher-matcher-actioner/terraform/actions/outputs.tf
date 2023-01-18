# Copyright (c) Meta Platforms, Inc. and affiliates.

output "writebacks_queue" {
  value = {
    url = aws_sqs_queue.writebacks_queue.id,
    arn = aws_sqs_queue.writebacks_queue.arn
  }
}

output "action_evaluator_function_name" {
  value = aws_lambda_function.action_evaluator.function_name
}

output "action_performer_function_name" {
  value = aws_lambda_function.action_performer.function_name
}

output "action_performer_iam_role_arn" {
  value = aws_iam_role.action_performer.arn
}

output "writebacker_function_name" {
  value = aws_lambda_function.writebacker.function_name
}

output "matches_queue_name" {
  value = aws_sqs_queue.matches_queue.name
}

output "matches_dlq_name" {
  value = aws_sqs_queue.matches_queue_dlq.name
}

output "actions_queue_name" {
  value = aws_sqs_queue.actions_queue.name
}

output "actions_dlq_name" {
  value = aws_sqs_queue.actions_queue_dlq.name
}

output "writebacks_queue_name" {
  value = aws_sqs_queue.writebacks_queue.name
}

output "writebacks_dlq_name" {
  value = aws_sqs_queue.writebacks_queue_dlq.name
}
