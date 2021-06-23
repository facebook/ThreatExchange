# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

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

output "writebacker_function_name" {
  value = aws_lambda_function.writebacker.function_name
}

output "matches_queue_name" {
  value = aws_sqs_queue.matches_queue.name
}

output "actions_queue_name" {
  value = aws_sqs_queue.actions_queue.name
}

output "writebacks_queue_name" {
  value = aws_sqs_queue.writebacks_queue.name
}
