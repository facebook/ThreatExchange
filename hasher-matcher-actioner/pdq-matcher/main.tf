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

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "pdq_matcher_lambda_role" {
  name               = "${var.prefix}_pdq_matcher_lambda_role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role_policy_attachment" "lambda_sqs_role_policy" {
  role       = aws_iam_role.pdq_matcher_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaSQSQueueExecutionRole"
}

resource "aws_lambda_function" "pdq_matcher_lambda" {
  function_name = "${var.prefix}_pdq_matcher_lambda"
  package_type  = "Image"
  role          = aws_iam_role.pdq_matcher_lambda_role.arn
  image_uri     = var.lambda_docker_uri
  image_config {
    command = [var.lambda_docker_command]
  }
  timeout = 300
  environment {
    variables = {
      PDQ_MATCHES_TOPIC_ARN = aws_sns_topic.pdq_matches.arn
    }
  }
}

resource "aws_lambda_event_source_mapping" "input" {
  event_source_arn                   = var.input_queue_arn
  function_name                      = aws_lambda_function.pdq_matcher_lambda.arn
  batch_size                         = 100
  maximum_batching_window_in_seconds = 30
}

resource "aws_sns_topic" "pdq_matches" {
  name_prefix = "${var.prefix}-pdq-matches"
}
