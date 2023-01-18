# Copyright (c) Meta Platforms, Inc. and affiliates.

/* Hashing Lambda Configuration Begins
 *
 * Pipe the submissions queue into the hashing lambda.
 */
resource "aws_lambda_function" "hashing_lambda" {
  function_name = "${var.prefix}_hasher"
  package_type  = "Image"
  role          = aws_iam_role.hashing_lambda_role.arn
  image_uri     = var.lambda_docker_info.uri

  image_config {
    command = ["hmalib.lambdas.hashing.lambda_handler"]
  }

  timeout     = 300
  memory_size = 512

  environment {
    variables = {
      DYNAMODB_TABLE      = var.datastore.name
      BANKS_TABLE         = var.banks_datastore.name
      METRICS_NAMESPACE   = var.metrics_namespace
      MEASURE_PERFORMANCE = var.measure_performance ? "True" : "False"
      HASHES_QUEUE_URL    = var.hashes_queue.url
      IMAGE_PREFIX        = var.image_data_storage.image_prefix
      HMA_CONFIG_TABLE    = var.config_table.name
    }
  }

  # vpc_config {
  #   security_group_ids = var.durable_fs_security_group_ids
  #   subnet_ids         = var.durable_fs_subnet_ids
  # }

  # file_system_config {
  #   local_mount_path = var.durable_fs_local_mount_path
  #   arn              = var.durable_fs_arn
  # }

  tags = merge(
    var.additional_tags,
    {
      Name = "HashingLambda"
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

resource "aws_iam_policy" "hashing_lambda_policy" {
  name_prefix = "${var.prefix}_hasher_policy"
  description = "Permissions for Hashing Lambda"
  policy      = data.aws_iam_policy_document.hashing_lambda.json
}
resource "aws_iam_role" "hashing_lambda_role" {
  name_prefix        = "${var.prefix}_hasher"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags = merge(
    var.additional_tags,
    {
      Name = "HashingLambda"
    }
  )
}

resource "aws_cloudwatch_log_group" "hashing_logs" {
  name              = "/aws/lambda/${aws_lambda_function.hashing_lambda.function_name}"
  retention_in_days = var.log_retention_in_days
  tags = merge(
    var.additional_tags,
    {
      Name = "HasherLambdaLogGroup"
    }
  )
}

data "aws_iam_policy_document" "hashing_lambda" {
  statement {
    effect    = "Allow"
    actions   = ["sqs:GetQueueAttributes", "sqs:ReceiveMessage", "sqs:DeleteMessage"]
    resources = [var.submissions_queue.arn]
  }
  statement {
    effect    = "Allow"
    actions   = ["sqs:SendMessage"]
    resources = [var.hashes_queue.arn]
  }
  statement {
    effect    = "Allow"
    actions   = ["dynamodb:PutItem", "dynamodb:UpdateItem"]
    resources = [var.datastore.arn, var.banks_datastore.arn]
  }
  statement {
    effect    = "Allow"
    actions   = ["dynamodb:GetItem", "dynamodb:Query", "dynamodb:Scan"]
    resources = [var.config_table.arn]
  }
  statement {
    effect    = "Allow"
    actions   = ["s3:GetObject"]
    resources = ["arn:aws:s3:::${var.image_data_storage.bucket_name}/${var.image_data_storage.image_prefix}*"]
  }
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]
    resources = ["${aws_cloudwatch_log_group.hashing_logs.arn}:*"]
  }
  statement {
    effect    = "Allow"
    actions   = ["cloudwatch:PutMetricData"]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy_attachment" "hashing_lambda_permissions" {
  role       = aws_iam_role.hashing_lambda_role.name
  policy_arn = aws_iam_policy.hashing_lambda_policy.arn
}

resource "aws_iam_role_policy_attachment" "AWSLambdaVPCAccessExecutionRole" {
  role       = aws_iam_role.hashing_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_lambda_event_source_mapping" "submissions_to_hasher" {
  event_source_arn = var.submissions_queue.arn
  function_name    = aws_lambda_function.hashing_lambda.arn

  # Evidently, once set, batch-size and max-batching-window must always
  # be provided. Else terraform warns.
  batch_size                         = 10
  maximum_batching_window_in_seconds = 10
}
/* Hashing Lambda Configuration Ends */
