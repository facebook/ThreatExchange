# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

output "lambda_arn" {
  value = aws_lambda_function.pdq_matcher_lambda.arn
}

output "output_topic_arn" {
  value = aws_sns_topic.pdq_matches.arn
}
