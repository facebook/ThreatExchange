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


# Ability to read from s3 bucket to load up hash_index
data "aws_iam_policy_document" "lambda_s3_access" {
  statement {
    effect    = "Allow"
    actions   = ["s3:GetObject"]
    resources = ["${var.s3_index_arn}*"]
  }
}

resource "aws_iam_policy" "lambda_s3_access" {
  name_prefix = "${var.prefix}_pdq_matcher_s3_access"
  description = "PDQ Matcher access to index(es) in S3"
  policy      = data.aws_iam_policy_document.lambda_s3_access.json
}

resource "aws_iam_role_policy_attachment" "lambda_s3_access" {
  role       = aws_iam_role.pdq_matcher_lambda_role.name
  policy_arn = aws_iam_policy.lambda_s3_access.arn
}

# Ability to publish to 'match found' sns topic
data "aws_iam_policy_document" "lambda_sns_publish" {
  statement {
    effect    = "Allow"
    actions   = ["SNS:Publish"]
    resources = [aws_sns_topic.pdq_matches.arn]
  }
}

resource "aws_iam_policy" "lambda_sns_publish" {
  name_prefix = "${var.prefix}_pdq_matcher_sns_publish"
  description = "PDQ Matcher access to publish to SNS"
  policy      = data.aws_iam_policy_document.lambda_sns_publish.json
}

resource "aws_iam_role_policy_attachment" "lambda_sns_publish" {
  role       = aws_iam_role.pdq_matcher_lambda_role.name
  policy_arn = aws_iam_policy.lambda_sns_publish.arn
}

resource "aws_lambda_function" "pdq_matcher_lambda" {
  function_name = "${var.prefix}_pdq_matcher_lambda"
  package_type  = "Image"
  role          = aws_iam_role.pdq_matcher_lambda_role.arn
  image_uri     = var.lambda_docker_uri
  image_config {
    command = [var.lambda_docker_command]
  }
  timeout     = 300
  memory_size = 512
  environment {
    variables = {
      PDQ_MATCHES_TOPIC_ARN = aws_sns_topic.pdq_matches.arn
      DATA_BUCKET           = var.s3_data_bucket_id
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
