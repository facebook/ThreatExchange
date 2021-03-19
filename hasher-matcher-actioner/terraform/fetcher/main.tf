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

### Lambda for fetcher ###

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
      THREAT_EXCHANGE_CONFIG_DYNAMODB  = aws_dynamodb_table.threatexchange_config.name
    }
  }
  tags = merge(
    var.additional_tags,
    {
      Name = "FetcherFunction"
    }
  )
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "${var.prefix}AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.fetcher.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.recurring_fetch.arn
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
  statement {
    effect    = "Allow"
    actions   = ["dynamodb:Scan"]
    resources = [aws_dynamodb_table.threatexchange_config.arn]
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

### AWS Cloud Watch Event to regularly fetch ###

# Pointer to function
resource "aws_cloudwatch_event_target" "fetcher" {
  arn  = aws_lambda_function.fetcher.arn
  rule = aws_cloudwatch_event_rule.recurring_fetch.name
}

# Rule that runs regularly
resource "aws_cloudwatch_event_rule" "recurring_fetch" {
  name                = "${var.prefix}RecurringThreatExchangeFetch"
  description         = "Fetch updates from ThreatExchange on a regular cadence"
  schedule_expression = "rate(${var.fetch_frequency_min} minutes)"
  role_arn            = aws_iam_role.fetcher_trigger.arn
}

# Role for the trigger
resource "aws_iam_role" "fetcher_trigger" {
  name_prefix        = "${var.prefix}_fetcher_trigger"
  assume_role_policy = data.aws_iam_policy_document.fetcher_trigger_assume_role.json

  tags = merge(
    var.additional_tags,
    {
      Name = "FetcherLambdaTriggerRole"
    }
  )
}

# Assume policy for trigger role allowing events.amazonaws.com to assume the role
data "aws_iam_policy_document" "fetcher_trigger_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }
  }
}

# Define a policy document to asign to the role
data "aws_iam_policy_document" "fetcher_trigger" {
  statement {
    actions   = ["lambda:InvokeFunction"]
    resources = ["*"]
    effect    = "Allow"
    condition {
      test     = "ArnLike"
      variable = "AWS:SourceArn"
      values   = [aws_cloudwatch_event_rule.recurring_fetch.arn]
    }
  }
}

# Create a permission policy from policy document
resource "aws_iam_policy" "fetcher_trigger" {
  name_prefix = "${var.prefix}_fetcher_trigger_role_policy"
  description = "Permissions for Recurring Fetcher Trigger"
  policy      = data.aws_iam_policy_document.fetcher_trigger.json
}

# Attach a permission policy to the fetech trigger role
resource "aws_iam_role_policy_attachment" "fetcher_trigger" {
  role       = aws_iam_role.fetcher_trigger.name
  policy_arn = aws_iam_policy.fetcher_trigger.arn
}

### Config storage ###

resource "aws_dynamodb_table" "threatexchange_config" {
  name         = "${var.prefix}-ThreatExchangeConfig"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "Name"

  attribute {
    name = "Name"
    type = "S"
  }

  tags = merge(
    var.additional_tags,
    {
      Name = "ThreatExchangeConfig"
    }
  )
}

### ThreatExchange API Token Secret ###

resource "aws_secretsmanager_secret" "api_token" {
  name                    = "threatexchange/${var.prefix}_api_tokens"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "api_token" {
  secret_id     = aws_secretsmanager_secret.api_token.id
  secret_string = var.te_api_token
}
