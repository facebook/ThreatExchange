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

locals {
  pdq_index_key = "${var.index_data_storage.index_folder_key}pdq_hashes.index"
  pdq_index_arn = "arn:aws:s3:::${var.index_data_storage.bucket_name}/${local.pdq_index_key}"
}

# PDQ Indexer

resource "aws_lambda_function" "pdq_indexer" {
  function_name = "${var.prefix}_pdq_indexer"
  package_type  = "Image"
  role          = aws_iam_role.pdq_indexer.arn
  image_uri     = var.lambda_docker_info.uri
  image_config {
    command = [var.lambda_docker_info.commands.indexer]
  }
  timeout     = 300
  memory_size = 512
  environment {
    variables = {
      THREAT_EXCHANGE_DATA_BUCKET_NAME   = var.threat_exchange_data.bucket_name
      THREAT_EXCHANGE_DATA_FOLDER        = var.threat_exchange_data.data_folder
      THREAT_EXCHANGE_PDQ_FILE_EXTENSION = var.threat_exchange_data.pdq_file_extension
      INDEXES_BUCKET_NAME                = var.index_data_storage.bucket_name
      PDQ_INDEX_KEY                      = local.pdq_index_key
    }
  }
  tags = merge(
    var.additional_tags,
    {
      Name = "PDQIndexerFunction"
    }
  )
}

resource "aws_cloudwatch_log_group" "pdq_indexer" {
  name              = "/aws/lambda/${aws_lambda_function.pdq_indexer.function_name}"
  retention_in_days = var.log_retention_in_days
  tags = merge(
    var.additional_tags,
    {
      Name = "PDQIndexerLambdaLogGroup"
    }
  )
}

resource "aws_iam_role" "pdq_indexer" {
  name_prefix        = "${var.prefix}_pdq_indexer"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags = merge(
    var.additional_tags,
    {
      Name = "PDQIndexerLambdaRole"
    }
  )
}

data "aws_iam_policy_document" "pdq_indexer" {
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
    resources = [local.pdq_index_arn]
  }
  statement {
    effect    = "Allow"
    actions   = ["s3:PutObject"]
    resources = [local.pdq_index_arn]
  }
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]
    resources = ["${aws_cloudwatch_log_group.pdq_indexer.arn}:*"]
  }
  statement {
    effect    = "Allow"
    actions   = ["cloudwatch:PutMetricData"]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "pdq_indexer" {
  name_prefix = "${var.prefix}_pdq_indexer_role_policy"
  description = "Permissions for PDQ Indexer Lambda"
  policy      = data.aws_iam_policy_document.pdq_indexer.json
}

resource "aws_iam_role_policy_attachment" "pdq_indexer" {
  role       = aws_iam_role.pdq_indexer.name
  policy_arn = aws_iam_policy.pdq_indexer.arn
}

resource "aws_sns_topic_subscription" "pdq_indexer" {
  topic_arn = var.threat_exchange_data.notification_topic
  protocol  = "lambda"
  endpoint  = aws_lambda_function.pdq_indexer.arn
}

resource "aws_lambda_permission" "pdq_indexer" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.pdq_indexer.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = var.threat_exchange_data.notification_topic
}

# PDQ Hasher

resource "aws_sqs_queue" "hashes_queue" {
  name_prefix                = "${var.prefix}-pdq-hashes"
  visibility_timeout_seconds = 300
  message_retention_seconds  = 1209600
  tags = merge(
    var.additional_tags,
    {
      Name = "PDQHashesQueue"
    }
  )
}

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
      DYNAMODB_TABLE       = var.datastore.name
      MEASURE_PERFORMANCE  = var.measure_performance ? "True" : "False"
      METRICS_NAMESPACE    = var.metrics_namespace
    }
  }
  tags = merge(
    var.additional_tags,
    {
      Name = "PDQHasherFunction"
    }
  )
}

resource "aws_cloudwatch_log_group" "pdq_hasher" {
  name              = "/aws/lambda/${aws_lambda_function.pdq_hasher.function_name}"
  retention_in_days = var.log_retention_in_days
  tags = merge(
    var.additional_tags,
    {
      Name = "PDQHasherLambdaLogGroup"
    }
  )
}

resource "aws_iam_role" "pdq_hasher" {
  name_prefix        = "${var.prefix}_pdq_hasher"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags = merge(
    var.additional_tags,
    {
      Name = "PDQHasherLambdaRole"
    }
  )
}

data "aws_iam_policy_document" "pdq_hasher" {
  statement {
    effect    = "Allow"
    actions   = ["sqs:GetQueueAttributes", "sqs:ReceiveMessage", "sqs:DeleteMessage"]
    resources = [var.images_input.input_queue]
  }
  statement {
    effect    = "Allow"
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.hashes_queue.arn]
  }
  statement {
    effect    = "Allow"
    actions   = ["s3:GetObject"]
    resources = var.images_input.resource_list
  }
  statement {
    effect    = "Allow"
    actions   = ["dynamodb:PutItem", "dynamodb:UpdateItem"]
    resources = [var.datastore.arn]
  }
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]
    resources = ["${aws_cloudwatch_log_group.pdq_hasher.arn}:*"]
  }
  statement {
    effect    = "Allow"
    actions   = ["cloudwatch:PutMetricData"]
    resources = ["*"]
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
  event_source_arn = var.images_input.input_queue
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
      INDEXES_BUCKET_NAME   = var.index_data_storage.bucket_name
      PDQ_INDEX_KEY         = local.pdq_index_key
      DYNAMODB_TABLE        = var.datastore.name
      MEASURE_PERFORMANCE   = var.measure_performance ? "True" : "False"
      METRICS_NAMESPACE     = var.metrics_namespace
      HMA_CONFIG_TABLE      = var.config_table.name
    }
  }
  tags = merge(
    var.additional_tags,
    {
      Name = "PDQMatcherFunction"
    }
  )
}

resource "aws_cloudwatch_log_group" "pdq_matcher" {
  name              = "/aws/lambda/${aws_lambda_function.pdq_matcher.function_name}"
  retention_in_days = var.log_retention_in_days
  tags = merge(
    var.additional_tags,
    {
      Name = "PDQMatcherLambdaLogGroup"
    }
  )
}

resource "aws_iam_role" "pdq_matcher" {
  name_prefix        = "${var.prefix}_pdq_matcher"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags = merge(
    var.additional_tags,
    {
      Name = "PDQMatcherLambdaRole"
    }
  )
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
    resources = [local.pdq_index_arn]
  }
  statement {
    effect    = "Allow"
    actions   = ["dynamodb:PutItem", "dynamodb:UpdateItem"]
    resources = [var.datastore.arn]
  }
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]
    resources = ["${aws_cloudwatch_log_group.pdq_matcher.arn}:*"]
  }
  statement {
    effect    = "Allow"
    actions   = ["cloudwatch:PutMetricData"]
    resources = ["*"]
  }

  statement {
    effect    = "Allow"
    actions   = ["dynamodb:GetItem", "dynamodb:Query", "dynamodb:Scan"]
    resources = [var.config_table.arn]
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
  batch_size                         = var.queue_batch_size
  maximum_batching_window_in_seconds = var.queue_window_in_seconds
}


resource "null_resource" "provide_sample_pdq_data_holidays" {
  # To force-update on existing deployment, taint and apply terraform again
  # $ terraform taint module.hashing_data.null_resource.provide_sample_pdq_data_holidays
  # $ terraform apply

  # To get a sensible privacy group value, we reverse engineer the filename split at
  # hmalib.common.s3_adapters.ThreatExchangeS3Adapter._parse_file at line 118
  depends_on = [
    aws_lambda_function.pdq_indexer
  ]

  provisioner "local-exec" {
    environment = {
      PRIVACY_GROUP = "inria-holidays-test"
    }

    command = "aws s3 cp ../sample_data/holidays-jpg1-pdq-hashes.csv s3://${var.threat_exchange_data.bucket_name}/${var.threat_exchange_data.data_folder}$PRIVACY_GROUP.holidays-jpg1-pdq-hashes.pdq.te"
  }
}
