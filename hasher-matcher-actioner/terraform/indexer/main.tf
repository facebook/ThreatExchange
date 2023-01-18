# Copyright (c) Meta Platforms, Inc. and affiliates.

# First define the Indexing Schedule
resource "aws_cloudwatch_event_rule" "indexing_trigger" {
  name                = "${var.prefix}-RecurringIndexBuild"
  description         = "Rebuild Index on a regular cadence"
  schedule_expression = "rate(${var.indexer_frequency})"
  role_arn            = aws_iam_role.indexing_trigger.arn
}

resource "aws_iam_role" "indexing_trigger" {
  name_prefix        = "${var.prefix}_indexing_trigger"
  assume_role_policy = data.aws_iam_policy_document.indexing_trigger_assume_role.json

  tags = merge(
    var.additional_tags,
    {
      Name = "FetcherLambdaTriggerRole"
    }
  )
}

data "aws_iam_policy_document" "indexing_trigger_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }
  }
}

## Define a policy document to asign to the role
data "aws_iam_policy_document" "indexing_trigger" {
  statement {
    actions   = ["lambda:InvokeFunction"]
    resources = [aws_lambda_function.indexer.arn]
    effect    = "Allow"
    condition {
      test     = "ArnLike"
      variable = "AWS:SourceArn"
      values   = [aws_cloudwatch_event_rule.indexing_trigger.arn]
    }
  }
}

## Create a permission policy from policy document
resource "aws_iam_policy" "indexing_trigger" {
  name_prefix = "${var.prefix}_indexing_trigger_role_policy"
  description = "Permissions for Indexing Schedule"
  policy      = data.aws_iam_policy_document.indexing_trigger.json
}

## Attach a permission policy to the indexing trigger role
resource "aws_iam_role_policy_attachment" "indexing_trigger" {
  role       = aws_iam_role.indexing_trigger.name
  policy_arn = aws_iam_policy.indexing_trigger.arn
}

## Connect rule to function invocation
resource "aws_cloudwatch_event_target" "indexer" {
  arn  = aws_lambda_function.indexer.arn
  rule = aws_cloudwatch_event_rule.indexing_trigger.name
}



# Then define the Indexing Function / Lambda etc.
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

resource "aws_lambda_function" "indexer" {
  function_name = "${var.prefix}_indexer"
  package_type  = "Image"
  role          = aws_iam_role.indexer.arn
  image_uri     = var.lambda_docker_info.uri
  image_config {
    command = [var.lambda_docker_info.commands.indexer]
  }
  timeout     = 720 # 12 minutes
  memory_size = 5120

  ephemeral_storage {
    size = 5120
  }

  environment {
    variables = {
      THREAT_EXCHANGE_DATA_BUCKET_NAME = var.threat_exchange_data.bucket_name
      THREAT_EXCHANGE_DATA_FOLDER      = var.threat_exchange_data.data_folder
      INDEXES_BUCKET_NAME              = var.index_data_storage.bucket_name
      MEASURE_PERFORMANCE              = var.measure_performance ? "True" : "False"
      HMA_CONFIG_TABLE                 = var.config_table.name
      BANKS_TABLE                      = var.banks_datastore.name
    }
  }
  tags = merge(
    var.additional_tags,
    {
      Name = "IndexerFunction"
    }
  )
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "${var.prefix}AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.indexer.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.indexing_trigger.arn
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
    effect    = "Allow"
    actions   = ["dynamodb:GetItem", "dynamodb:Query", "dynamodb:Scan", "dynamodb:PutItem", "dynamodb:UpdateItem"]
    resources = ["${var.banks_datastore.arn}*"]
  }
  statement {
    effect    = "Allow"
    actions   = ["dynamodb:GetItem", "dynamodb:Query", "dynamodb:Scan", "dynamodb:PutItem", "dynamodb:DeleteItem"]
    resources = [var.config_table.arn]
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

resource "null_resource" "provide_sample_pdq_data_holidays" {
  # To force-update on existing deployment, taint and apply terraform again
  # $ terraform taint module.indexer.null_resource.provide_sample_pdq_data_holidays
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

    command = "aws s3 cp ../sample_data/holidays-jpg1-pdq-hashes.csv s3://${var.threat_exchange_data.bucket_name}/${var.threat_exchange_data.data_folder}$PRIVACY_GROUP.hash_pdq.te"
  }
}
