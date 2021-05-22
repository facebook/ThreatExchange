# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

locals {
  common_tags = {
    "HMAPrefix" = var.prefix
  }
}

# Define a queue for the InputSNS topic to push messages to.
resource "aws_sqs_queue" "match_counter_queue" {
  name_prefix                = "${var.prefix}-match-counter"
  visibility_timeout_seconds = 300
  message_retention_seconds  = 1209600
  tags = merge(
    var.additional_tags,
    local.common_tags
  )
}

data "aws_iam_policy_document" "match_counter_queue" {
  statement {
    effect    = "Allow"
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.match_counter_queue.arn]

    principals {
      type        = "Service"
      identifiers = ["sns.amazonaws.com"]
    }
    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = [var.matches_sns_topic_arn]
    }
  }
}

resource "aws_sqs_queue_policy" "match_counter_queue" {
  queue_url = aws_sqs_queue.match_counter_queue.id
  policy    = data.aws_iam_policy_document.match_counter_queue.json
}
# Blocks dedicated to the queue ends.

# Connects InputSNS -> SQS Queue. InputSNS is an externally configured SNS Topic
# which collects matches from various matcher lambdas.
resource "aws_sns_topic_subscription" "new_matches_topic" {
  topic_arn = var.matches_sns_topic_arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.match_counter_queue.arn
}

# Define lambda
resource "aws_lambda_function" "match_counter" {
  function_name = "${var.prefix}_match_counter"
  package_type  = "Image"
  role          = aws_iam_role.match_counter_lambda_role.arn
  image_uri     = var.lambda_docker_info.uri
  image_config {
    command = [var.lambda_docker_info.commands.match_counter]
  }
  timeout     = 300
  memory_size = 512
  environment {
    variables = {
      DYNAMODB_TABLE      = var.datastore.name
      MEASURE_PERFORMANCE = var.measure_performance ? "True" : "False"
    }
  }
  tags = merge(
    var.additional_tags,
    {
      Name = "MatchCounter"
    }
  )
}

resource "aws_cloudwatch_log_group" "match_counter" {
  name              = "/aws/lambda/${aws_lambda_function.match_counter.function_name}"
  retention_in_days = var.log_retention_in_days
  tags = merge(
    var.additional_tags,
    {
      Name = "MatchCounterLambdaLogGroup"
    }
  )
}

# Lambda permisions, this goes on for a while.
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

resource "aws_iam_role" "match_counter_lambda_role" {
  name_prefix        = "${var.prefix}_match_counter"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags = merge(
    var.additional_tags,
    {
      Name = "MatchCounterLambdaRole"
    }
  )
}

data "aws_iam_policy_document" "match_counter_iam_policy_document" {
  statement {
    effect    = "Allow"
    actions   = ["dynamodb:UpdateItem"]
    resources = ["${var.datastore.arn}*"]
  }
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]
    resources = ["${aws_cloudwatch_log_group.match_counter.arn}:*"]
  }
  statement {
    effect    = "Allow"
    actions   = ["sqs:GetQueueAttributes", "sqs:ReceiveMessage", "sqs:DeleteMessage"]
    resources = [aws_sqs_queue.match_counter_queue.arn]
  }
}

resource "aws_iam_policy" "match_counter_iam_policy" {
  name_prefix = "${var.prefix}_match_counter_iam_policy"
  description = "Permissions for Match Counter Lambda"
  policy      = data.aws_iam_policy_document.match_counter_iam_policy_document.json
}

resource "aws_iam_role_policy_attachment" "match_counter" {
  role       = aws_iam_role.match_counter_lambda_role.name
  policy_arn = aws_iam_policy.match_counter_iam_policy.arn
}
# Lambda permissions finally ends.

# Connect lambda to SQS queue
resource "aws_lambda_event_source_mapping" "match_counter_queue_to_counter_lambda" {
  event_source_arn                   = aws_sqs_queue.match_counter_queue.arn
  function_name                      = aws_lambda_function.match_counter.arn
  batch_size                         = 100
  maximum_batching_window_in_seconds = 30
}
