# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

terraform {
  required_providers {
    aws = "~> 3.0"
  }
}

provider "aws" {
  region  = var.region
  profile = var.profile
}

resource "aws_iam_role" "pdq_hasher_lambda_role" {
  name = "${var.prefix}_pdq_hasher_lambda_role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
  EOF
}

resource "aws_iam_role_policy_attachment" "lambda_sqs_role_policy" {
  role       = aws_iam_role.pdq_hasher_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaSQSQueueExecutionRole"
}

resource "aws_lambda_function" "pdq_hasher_lambda" {
  function_name = "${var.prefix}_pdq_hasher_lambda"
  package_type  = "Image"
  role          = aws_iam_role.pdq_hasher_lambda_role.arn
  image_uri     = var.lambda_docker_uri
  image_config {
    command = [var.lambda_docker_command]
  }

  environment {
    variables = {
      PDQ_HASHES_TOPIC_ARN = aws_sns_topic.pdq_hashes.arn
    }
  }
}

resource "aws_sqs_queue" "pdq_hasher_new_file_queue" {
  name_prefix                = "${var.prefix}-pdq-hasher"
  visibility_timeout_seconds = 60
  message_retention_seconds  = 1209600
}

resource "aws_lambda_event_source_mapping" "input" {
  event_source_arn = aws_sqs_queue.pdq_hasher_new_file_queue.arn
  function_name    = aws_lambda_function.pdq_hasher_lambda.arn
}

resource "aws_sns_topic" "pdq_hashes" {
  name_prefix = "${var.prefix}-pdq-hashes"
}
