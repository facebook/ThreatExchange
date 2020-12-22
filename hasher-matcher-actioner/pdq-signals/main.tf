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

resource "aws_sqs_queue" "hashes_queue" {
  name_prefix                = "${var.prefix}-pdq-hashes"
  visibility_timeout_seconds = 300
  message_retention_seconds  = 1209600
}

# PDQ Hasher
resource "aws_lambda_function" "pdq_hasher" {
  function_name = "${var.prefix}_pdq_hasher"
  package_type  = "Image"
  role          = aws_iam_role.pdq_hasher.arn
  image_uri     = var.lambda_docker_info.uri
  image_config {
    command = [var.lambda_docker_info.commands.hasher]
  }
  timeout     = 300
  memory_size = 512
  environment {
    variables = {
      PDQ_HASHES_QUEUE_URL = aws_sqs_queue.hashes_queue.id
    }
  }
}

resource "aws_iam_role" "pdq_hasher" {
  name_prefix        = "${var.prefix}_pdq_hasher"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

data "aws_iam_policy_document" "pdq_hasher" {
  statement {
    effect    = "Allow"
    actions   = ["sqs:GetQueueAttributes", "sqs:ReceiveMessage", "sqs:DeleteMessage"]
    resources = [var.images_input_queue_arn]
  }
  statement {
    effect    = "Allow"
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.hashes_queue.arn]
  }
  statement {
    effect    = "Allow"
    actions   = ["s3:GetObject"]
    resources = var.image_resource_list
  }
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]
    resources = ["arn:aws:logs:*:*:*"]
  }
}

resource "aws_iam_policy" "pdq_hasher" {
  name_prefix = "${var.prefix}_pdq_hasher_role_policy"
  description = "Permissions for PDQ Hasher Lambda"
  policy      = data.aws_iam_policy_document.pdq_hasher.json
}

resource "aws_iam_role_policy_attachment" "pdq_hasher" {
  role       = aws_iam_role.pdq_hasher.name
  policy_arn = aws_iam_policy.pdq_hasher.arn
}

resource "aws_lambda_event_source_mapping" "pdq_hasher" {
  event_source_arn = var.images_input_queue_arn
  function_name    = aws_lambda_function.pdq_hasher.arn
}

# PDQ Matcher

resource "aws_lambda_function" "pdq_matcher" {
  function_name = "${var.prefix}_pdq_matcher"
  package_type  = "Image"
  role          = aws_iam_role.pdq_matcher.arn
  image_uri     = var.lambda_docker_info.uri
  image_config {
    command = [var.lambda_docker_info.commands.matcher]
  }
  timeout     = 300
  memory_size = 512
  environment {
    variables = {
      PDQ_MATCHES_TOPIC_ARN = var.matches_sns_topic_arn
      DATA_BUCKET           = var.s3_data_bucket_id
    }
  }
}

resource "aws_iam_role" "pdq_matcher" {
  name_prefix        = "${var.prefix}_pdq_matcher"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

data "aws_iam_policy_document" "pdq_matcher" {
  statement {
    effect    = "Allow"
    actions   = ["sqs:GetQueueAttributes", "sqs:ReceiveMessage", "sqs:DeleteMessage"]
    resources = [aws_sqs_queue.hashes_queue.arn]
  }
  statement {
    effect    = "Allow"
    actions   = ["SNS:Publish"]
    resources = [var.matches_sns_topic_arn]
  }
  statement {
    effect    = "Allow"
    actions   = ["s3:GetObject"]
    resources = ["${var.s3_index_arn}*"]
  }
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]
    resources = ["arn:aws:logs:*:*:*"]
  }
}

resource "aws_iam_policy" "pdq_matcher" {
  name_prefix = "${var.prefix}_pdq_hasher_role_policy"
  description = "Permissions for PDQ Matcher Lambda"
  policy      = data.aws_iam_policy_document.pdq_matcher.json
}

resource "aws_iam_role_policy_attachment" "pdq_matcher" {
  role       = aws_iam_role.pdq_matcher.name
  policy_arn = aws_iam_policy.pdq_matcher.arn
}

resource "aws_lambda_event_source_mapping" "pdq_matcher" {
  event_source_arn                   = aws_sqs_queue.hashes_queue.arn
  function_name                      = aws_lambda_function.pdq_matcher.arn
  batch_size                         = 100
  maximum_batching_window_in_seconds = 30
}
