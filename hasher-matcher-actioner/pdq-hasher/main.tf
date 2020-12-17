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

resource "aws_iam_role" "pdq_hasher_lambda_role" {
  name               = "${var.prefix}_pdq_hasher_lambda_role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role_policy_attachment" "lambda_sqs_role_policy" {
  role       = aws_iam_role.pdq_hasher_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaSQSQueueExecutionRole"
}

data "aws_iam_policy_document" "lambda_s3_access" {
  statement {
    effect    = "Allow"
    actions   = ["s3:GetObject"]
    resources = ["${var.s3_images_arn}*"]
  }
}

resource "aws_iam_policy" "lambda_s3_access" {
  name_prefix = "${var.prefix}_pdq_hasher_s3_access"
  description = "PDQ Hasher access to images in S3"
  policy      = data.aws_iam_policy_document.lambda_s3_access.json
}

resource "aws_iam_role_policy_attachment" "lambda_s3_access" {
  role       = aws_iam_role.pdq_hasher_lambda_role.name
  policy_arn = aws_iam_policy.lambda_s3_access.arn
}

data "aws_iam_policy_document" "lambda_sns_publish" {
  statement {
    effect    = "Allow"
    actions   = ["SNS:Publish"]
    resources = [aws_sns_topic.pdq_hashes.arn]
  }
}

resource "aws_iam_policy" "lambda_sns_publish" {
  name_prefix = "${var.prefix}_pdq_hasher_sns_publish"
  description = "PDQ Hasher access to publish to SNS"
  policy      = data.aws_iam_policy_document.lambda_sns_publish.json
}

resource "aws_iam_role_policy_attachment" "lambda_sns_publish" {
  role       = aws_iam_role.pdq_hasher_lambda_role.name
  policy_arn = aws_iam_policy.lambda_sns_publish.arn
}

resource "aws_lambda_function" "pdq_hasher_lambda" {
  function_name = "${var.prefix}_pdq_hasher_lambda"
  package_type  = "Image"
  role          = aws_iam_role.pdq_hasher_lambda_role.arn
  image_uri     = var.lambda_docker_uri
  image_config {
    command = [var.lambda_docker_command]
  }
  timeout = 300
  memory_size = 512
  environment {
    variables = {
      PDQ_HASHES_TOPIC_ARN = aws_sns_topic.pdq_hashes.arn
    }
  }
}

resource "aws_lambda_event_source_mapping" "input" {
  event_source_arn = var.input_queue_arn
  function_name    = aws_lambda_function.pdq_hasher_lambda.arn
}

resource "aws_sns_topic" "pdq_hashes" {
  name_prefix = "${var.prefix}-pdq-hashes"
}
