# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

locals {
  common_tags = {
    "HMAPrefix" = var.prefix
  }
}

# Define a queue for the InputSNS topic to push messages to.
resource "aws_sqs_queue" "matches_queue" {
  name_prefix                = "${var.prefix}-matches-"
  visibility_timeout_seconds = 300
  message_retention_seconds  = 1209600
  tags = merge(
    var.additional_tags,
    local.common_tags
  )
}

data "aws_iam_policy_document" "matches_queue" {
  statement {
    effect    = "Allow"
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.matches_queue.arn]

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

resource "aws_sqs_queue_policy" "matches_queue" {
  queue_url = aws_sqs_queue.matches_queue.id
  policy    = data.aws_iam_policy_document.matches_queue.json
}
# Blocks dedicated to the queue ends.

# Connects InputSNS -> SQS Queue. InputSNS is an externally configured SNS Topic
# which collects matches from various matcher lambdas.
resource "aws_sns_topic_subscription" "new_matches_topic" {
  topic_arn = var.matches_sns_topic_arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.matches_queue.arn
}

# Create a lambda for evaluating which actions to be performed as a result
# of matches. Be prepared, quite a few blocks ahead.
resource "aws_lambda_function" "action_evaluator" {
  function_name = "${var.prefix}_action_evaluator"
  package_type  = "Image"
  role          = aws_iam_role.actioner.arn
  image_uri     = var.lambda_docker_info.uri

  image_config {
    command = [var.lambda_docker_info.commands.action_evaluator]
  }

  timeout     = 300
  memory_size = 512
}

# Create a lambda for performing actions in response to matches, after they are evaluated by
# the action evaluator.
resource "aws_lambda_function" "action_performer" {
  function_name = "${var.prefix}_action_performer"
  package_type  = "Image"
  role          = aws_iam_role.actioner.arn
  image_uri     = var.lambda_docker_info.uri

  image_config {
    command = [var.lambda_docker_info.commands.action_performer]
  }

  timeout     = 300
  memory_size = 512
}

resource "aws_cloudwatch_log_group" "action_performer" {
  name              = "/aws/lambda/${aws_lambda_function.action_performer.function_name}"
  retention_in_days = var.log_retention_in_days
  tags = merge(
    var.additional_tags,
    {
      Name = "ActionPerformerLambdaLogGroup"
    }
  )
}

resource "aws_cloudwatch_log_group" "action_evaluator" {
  name              = "/aws/lambda/${aws_lambda_function.action_evaluator.function_name}"
  retention_in_days = var.log_retention_in_days
  tags = merge(
    var.additional_tags,
    {
      Name = "ActionEvaluatorLambdaLogGroup"
    }
  )
}

# Currently both the action_evaluator and action_performer lambda
# use this same iam role+policy. We may need to split this later
resource "aws_iam_role" "actioner" {
  name_prefix        = "${var.prefix}_actioner"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags               = var.additional_tags
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

resource "aws_iam_policy" "actioner" {
  name_prefix = "${var.prefix}_actioner_role_policy"
  policy      = data.aws_iam_policy_document.actioner.json
}


data "aws_iam_policy_document" "actioner" {
  statement {
    effect    = "Allow"
    actions   = ["sqs:GetQueueAttributes", "sqs:ReceiveMessage", "sqs:DeleteMessage"]
    resources = [aws_sqs_queue.matches_queue.arn]
  }
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]
    resources = [
      "${aws_cloudwatch_log_group.action_performer.arn}:*",
      "${aws_cloudwatch_log_group.action_evaluator.arn}:*",
    ]
  }
  statement {
    effect    = "Allow"
    actions   = ["cloudwatch:PutMetricData"]
    resources = ["*"]
  }
  statement {
    effect    = "Allow"
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [var.te_api_token_secret.arn]
  }
}

resource "aws_iam_role_policy_attachment" "actioner" {
  role       = aws_iam_role.actioner.name
  policy_arn = aws_iam_policy.actioner.arn
}
# That's the end of blocks dedicated to the lambdas alone

# Now, connect SQS -> Lambda
resource "aws_lambda_event_source_mapping" "matches_queue_to_action_evaluator" {
  event_source_arn                   = aws_sqs_queue.matches_queue.arn
  function_name                      = aws_lambda_function.action_evaluator.arn
  batch_size                         = 100
  maximum_batching_window_in_seconds = 30
}
