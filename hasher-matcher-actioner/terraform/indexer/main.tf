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

#  Indexer

resource "aws_lambda_function" "indexer" {
  function_name = "${var.prefix}_indexer"
  package_type  = "Image"
  role          = aws_iam_role.indexer.arn
  image_uri     = var.lambda_docker_info.uri
  image_config {
    command = [var.lambda_docker_info.commands.indexer]
  }
  timeout     = 300
  memory_size = 512

  environment {
    variables = {
      THREAT_EXCHANGE_DATA_BUCKET_NAME = var.threat_exchange_data.bucket_name
      THREAT_EXCHANGE_DATA_FOLDER      = var.threat_exchange_data.data_folder
      INDEXES_BUCKET_NAME              = var.index_data_storage.bucket_name
      MEASURE_PERFORMANCE              = var.measure_performance ? "True" : "False"
    }
  }
  tags = merge(
    var.additional_tags,
    {
      Name = "IndexerFunction"
    }
  )
}

resource "aws_cloudwatch_log_group" "indexer" {
  name              = "/aws/lambda/${aws_lambda_function.indexer.function_name}"
  retention_in_days = var.log_retention_in_days
  tags = merge(
    var.additional_tags,
    {
      Name = "IndexerLambdaLogGroup"
    }
  )
}

resource "aws_iam_role" "indexer" {
  name_prefix        = "${var.prefix}_indexer"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags = merge(
    var.additional_tags,
    {
      Name = "IndexerLambdaRole"
    }
  )
}

data "aws_iam_policy_document" "indexer" {
  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject",
    ]
    resources = [
      "arn:aws:s3:::${var.threat_exchange_data.bucket_name}/${var.threat_exchange_data.data_folder}*",
    ]
  }
  statement {
    effect = "Allow"
    actions = [
      "s3:ListBucket"
    ]
    resources = [
      "arn:aws:s3:::${var.threat_exchange_data.bucket_name}",
    ]
  }
  statement {
    effect    = "Allow"
    actions   = ["s3:PutObject"]
    resources = ["arn:aws:s3:::${var.index_data_storage.bucket_name}/index/*"]
  }
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]
    resources = ["${aws_cloudwatch_log_group.indexer.arn}:*"]
  }
  statement {
    effect    = "Allow"
    actions   = ["cloudwatch:PutMetricData"]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "indexer" {
  name_prefix = "${var.prefix}_indexer_role_policy"
  description = "Permissions for Indexer Lambda"
  policy      = data.aws_iam_policy_document.indexer.json
}

resource "aws_iam_role_policy_attachment" "indexer" {
  role       = aws_iam_role.indexer.name
  policy_arn = aws_iam_policy.indexer.arn
}

resource "aws_sns_topic_subscription" "indexer" {
  topic_arn = var.threat_exchange_data.notification_topic
  protocol  = "lambda"
  endpoint  = aws_lambda_function.indexer.arn
}

resource "aws_lambda_permission" "indexer" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.indexer.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = var.threat_exchange_data.notification_topic
}

resource "null_resource" "provide_sample_pdq_data_holidays" {
  # To force-update on existing deployment, taint and apply terraform again
  # $ terraform taint module.hashing_data.null_resource.provide_sample_pdq_data_holidays
  # $ terraform apply

  # To get a sensible privacy group value, we reverse engineer the filename split at
  # hmalib.common.s3_adapters.ThreatExchangeS3Adapter._parse_file at line 118
  depends_on = [
    aws_lambda_function.indexer
  ]

  provisioner "local-exec" {
    environment = {
      PRIVACY_GROUP = "inria-holidays-test"
    }

    command = "aws s3 cp ../sample_data/holidays-jpg1-pdq-hashes.csv s3://${var.threat_exchange_data.bucket_name}/${var.threat_exchange_data.data_folder}$PRIVACY_GROUP.holidays-jpg1-pdq-hashes.hash_pdq.te"
  }
}
