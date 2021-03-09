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

# Lambda for fetcher

resource "aws_lambda_function" "fetcher" {
  function_name = "${var.prefix}_fetcher"
  package_type  = "Image"
  role          = aws_iam_role.fetcher.arn
  image_uri     = var.lambda_docker_info.uri
  image_config {
    command = [var.lambda_docker_info.commands.fetcher]
  }
  timeout     = 300
  memory_size = 512
  environment {
    variables = {
      THREAT_EXCHANGE_DATA_BUCKET_NAME = var.threat_exchange_data.bucket_name
    }
  }
  tags = merge(
    var.additional_tags,
    {
      Name = "FetcherFunction"
    }
  )
}

resource "aws_cloudwatch_log_group" "fetcher" {
  name              = "/aws/lambda/${aws_lambda_function.fetcher.function_name}"
  retention_in_days = var.log_retention_in_days
  tags = merge(
    var.additional_tags,
    {
      Name = "FetcherLambdaLogGroup"
    }
  )
}

resource "aws_iam_role" "fetcher" {
  name_prefix        = "${var.prefix}_fetcher"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags = merge(
    var.additional_tags,
    {
      Name = "FetcherLambdaRole"
    }
  )
}

data "aws_iam_policy_document" "fetcher" {
  statement {
    effect    = "Allow"
    actions   = ["s3:GetObject"]
    resources = ["arn:aws:s3:::${var.threat_exchange_data.bucket_name}/${var.threat_exchange_data.pdq_data_file_key}"]
  }
  statement {
    effect    = "Allow"
    actions   = ["s3:PutObject"]
    resources = ["arn:aws:s3:::${var.threat_exchange_data.bucket_name}/${var.threat_exchange_data.pdq_data_file_key}"]
  }
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]
    resources = ["${aws_cloudwatch_log_group.fetcher.arn}:*"]
  }
  statement {
    effect    = "Allow"
    actions   = ["cloudwatch:PutMetricData"]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "fetcher" {
  name_prefix = "${var.prefix}_fetcher_role_policy"
  description = "Permissions for Fetcher Lambda"
  policy      = data.aws_iam_policy_document.fetcher.json
}

resource "aws_iam_role_policy_attachment" "fetcher" {
  role       = aws_iam_role.fetcher.name
  policy_arn = aws_iam_policy.fetcher.arn
}


#resource "aws_lambda_permission" "fetcher" {
#  action        = "lambda:InvokeFunction"
#  function_name = aws_lambda_function.fetcher.function_name
#  principal     = "sns.amazonaws.com"
#  source_arn    = var.threat_exchange_data.notification_topic
#}