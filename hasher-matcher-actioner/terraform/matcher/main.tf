# Copyright (c) Meta Platforms, Inc. and affiliates.

/* Matching Lambda Configuration Begins
 *
 * Pipe the hashes queue into the matcher lambda.
 */
resource "aws_lambda_function" "matcher_lambda" {
  function_name = "${var.prefix}_matcher"
  package_type  = "Image"
  role          = aws_iam_role.matcher_lambda_role.arn
  image_uri     = var.lambda_docker_info.uri
  image_config {
    command = ["hmalib.lambdas.matcher.lambda_handler"]
  }

  timeout     = 300
  memory_size = 5120

  ephemeral_storage {
    size = 5120
  }

  environment {
    variables = {
      DYNAMODB_TABLE      = var.datastore.name
      METRICS_NAMESPACE   = var.metrics_namespace
      MEASURE_PERFORMANCE = var.measure_performance ? "True" : "False"
      INDEXES_BUCKET_NAME = var.index_data_storage.bucket_name
      HMA_CONFIG_TABLE    = var.config_table.name
      MATCHES_TOPIC_ARN   = var.matches_topic_arn
      BANKS_TABLE         = var.banks_datastore.name
    }
  }

  tags = merge(
    var.additional_tags,
    {
      Name = "MatchingLambda"
    }
  )
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

resource "aws_iam_policy" "matcher_lambda_policy" {
  name_prefix = "${var.prefix}_matcher_policy"
  description = "Permissions for Matching Lambda"
  policy      = data.aws_iam_policy_document.matcher_lambda.json
}

resource "aws_iam_role" "matcher_lambda_role" {
  name_prefix        = "${var.prefix}_matcher"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags = merge(
    var.additional_tags,
    {
      Name = "MatchingLambda"
    }
  )
}

resource "aws_cloudwatch_log_group" "matcher_logs" {
  name              = "/aws/lambda/${aws_lambda_function.matcher_lambda.function_name}"
  retention_in_days = var.log_retention_in_days
  tags = merge(
    var.additional_tags,
    {
      Name = "MatcherLambdaLogGroup"
    }
  )
}

data "aws_iam_policy_document" "matcher_lambda" {
  statement {
    effect    = "Allow"
    actions   = ["sqs:GetQueueAttributes", "sqs:ReceiveMessage", "sqs:DeleteMessage"]
    resources = [var.hashes_queue.arn]
  }
  statement {
    effect    = "Allow"
    actions   = ["SNS:Publish"]
    resources = [var.matches_topic_arn]
  }
  statement {
    effect  = "Allow"
    actions = ["s3:GetObject"]
    resources = [
      "arn:aws:s3:::${var.index_data_storage.bucket_name}/${var.index_data_storage.index_folder_key}*"
    ]
  }
  statement {
    effect    = "Allow"
    actions   = ["dynamodb:PutItem", "dynamodb:UpdateItem"]
    resources = [var.datastore.arn]
  }
  statement {
    effect    = "Allow"
    actions   = ["dynamodb:GetItem", "dynamodb:Scan"]
    resources = [var.config_table.arn]
  }
  statement {
    effect    = "Allow"
    actions   = ["dynamodb:GetItem", "dynamodb:Query"]
    resources = ["${var.banks_datastore.arn}*"]
  }
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]
    resources = ["${aws_cloudwatch_log_group.matcher_logs.arn}:*"]
  }
  statement {
    effect    = "Allow"
    actions   = ["cloudwatch:PutMetricData"]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy_attachment" "matcher_lambda_permissions" {
  role       = aws_iam_role.matcher_lambda_role.name
  policy_arn = aws_iam_policy.matcher_lambda_policy.arn
}

resource "aws_lambda_event_source_mapping" "hashes_to_matcher" {
  event_source_arn = var.hashes_queue.arn
  function_name    = aws_lambda_function.matcher_lambda.arn

  # Evidently, once set, batch-size and max-batching-window must always
  # be provided. Else terraform warns.
  batch_size                         = 10
  maximum_batching_window_in_seconds = 10
}
/* Matching Lambda Configuration Ends */
