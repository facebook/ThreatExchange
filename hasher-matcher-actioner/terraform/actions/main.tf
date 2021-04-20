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

# Set up the queue for sending messages from the action evaluator to the action performer

resource "aws_sqs_queue" "actions_queue" {
  name_prefix                = "${var.prefix}-actions"
  visibility_timeout_seconds = 300
  message_retention_seconds  = 1209600
  tags = merge(
    var.additional_tags,
    {
      Name = "ActionsQueue"
    }
  )
}

# Set up the queue for sending messages from the action evaluator to the reactioner

resource "aws_sqs_queue" "reactions_queue" {
  name_prefix                = "${var.prefix}-reactions"
  visibility_timeout_seconds = 300
  message_retention_seconds  = 1209600
  tags = merge(
    var.additional_tags,
    {
      Name = "ReactionsQueue"
    }
  )
}

# Lambda functions

# Action evaluator evaluates which actions to perform as a result of a match.

resource "aws_lambda_function" "action_evaluator" {
  function_name = "${var.prefix}_action_evaluator"
  package_type  = "Image"
  role          = aws_iam_role.action_evaluator.arn
  image_uri     = var.lambda_docker_info.uri

  image_config {
    command = [var.lambda_docker_info.commands.action_evaluator]
  }

  timeout     = 300
  memory_size = 512

  environment {
    variables = {
      ACTIONS_QUEUE_URL = aws_sqs_queue.actions_queue.id,
      REACTIONS_QUEUE_URL = aws_sqs_queue.reactions_queue.id,
    }
  }
}

# Action performer performs actions decided on by the action evaluator.

resource "aws_lambda_function" "action_performer" {
  function_name = "${var.prefix}_action_performer"
  package_type  = "Image"
  role          = aws_iam_role.action_performer.arn
  image_uri     = var.lambda_docker_info.uri

  image_config {
    command = [var.lambda_docker_info.commands.action_performer]
  }

  timeout     = 300
  memory_size = 512
}

# Reactioner reacts to ThreatExchange.

resource "aws_lambda_function" "reactioner" {
  function_name = "${var.prefix}_reactioner"
  package_type  = "Image"
  role          = aws_iam_role.reactioner.arn
  image_uri     = var.lambda_docker_info.uri

  image_config {
    command = [var.lambda_docker_info.commands.reactioner]
  }

  timeout     = 300
  memory_size = 512
}

# Log groups

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

resource "aws_cloudwatch_log_group" "reactioner" {
  name              = "/aws/lambda/${aws_lambda_function.reactioner.function_name}"
  retention_in_days = var.log_retention_in_days
  tags = merge(
    var.additional_tags,
    {
      Name = "ReactionerLambdaLogGroup"
    }
  )
}

# Common "assume role" policy document

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

# Role and policy for action evaluator

resource "aws_iam_role" "action_evaluator" {
  name_prefix        = "${var.prefix}_action_evaluator"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags               = var.additional_tags
}

resource "aws_iam_policy" "action_evaluator" {
  name_prefix = "${var.prefix}_action_evaluator_role_policy"
  policy      = data.aws_iam_policy_document.action_evaluator.json
}

data "aws_iam_policy_document" "action_evaluator" {
  statement {
    effect    = "Allow"
    actions   = ["sqs:GetQueueAttributes", "sqs:ReceiveMessage", "sqs:DeleteMessage"]
    resources = [aws_sqs_queue.matches_queue.arn]
  }
  statement {
    effect    = "Allow"
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.actions_queue.arn, aws_sqs_queue.reactions_queue.arn]
  }
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]
    resources = ["${aws_cloudwatch_log_group.action_evaluator.arn}:*"]
  }
  statement {
    effect    = "Allow"
    actions   = ["cloudwatch:PutMetricData"]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy_attachment" "action_evaluator" {
  role       = aws_iam_role.action_evaluator.name
  policy_arn = aws_iam_policy.action_evaluator.arn
}

# Role and policy for action performer

resource "aws_iam_role" "action_performer" {
  name_prefix        = "${var.prefix}_action_performer"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags               = var.additional_tags
}

resource "aws_iam_policy" "action_performer" {
  name_prefix = "${var.prefix}_action_performer_role_policy"
  policy      = data.aws_iam_policy_document.action_performer.json
}

data "aws_iam_policy_document" "action_performer" {
  statement {
    effect    = "Allow"
    actions   = ["sqs:GetQueueAttributes", "sqs:ReceiveMessage", "sqs:DeleteMessage"]
    resources = [aws_sqs_queue.actions_queue.arn]
  }
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]
    resources = ["${aws_cloudwatch_log_group.action_performer.arn}:*"]
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

resource "aws_iam_role_policy_attachment" "action_performer" {
  role       = aws_iam_role.action_performer.name
  policy_arn = aws_iam_policy.action_performer.arn
}

# Role and policy for action reactioner

resource "aws_iam_role" "reactioner" {
  name_prefix        = "${var.prefix}_reactioner"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags               = var.additional_tags
}

resource "aws_iam_policy" "reactioner" {
  name_prefix = "${var.prefix}_reactioner_role_policy"
  policy      = data.aws_iam_policy_document.reactioner.json
}

data "aws_iam_policy_document" "reactioner" {
  statement {
    effect    = "Allow"
    actions   = ["sqs:GetQueueAttributes", "sqs:ReceiveMessage", "sqs:DeleteMessage"]
    resources = [aws_sqs_queue.reactions_queue.arn]
  }
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]
    resources = ["${aws_cloudwatch_log_group.reactioner.arn}:*"]
  }
  statement {
    effect    = "Allow"
    actions   = ["cloudwatch:PutMetricData"]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy_attachment" "reactioner" {
  role       = aws_iam_role.reactioner.name
  policy_arn = aws_iam_policy.reactioner.arn
}

# Connect sqs -> lambda

resource "aws_lambda_event_source_mapping" "matches_queue_to_action_evaluator" {
  event_source_arn                   = aws_sqs_queue.matches_queue.arn
  function_name                      = aws_lambda_function.action_evaluator.arn
  batch_size                         = 100
  maximum_batching_window_in_seconds = 30
}

resource "aws_lambda_event_source_mapping" "actions_queue_to_action_performer" {
  event_source_arn                   = aws_sqs_queue.actions_queue.arn
  function_name                      = aws_lambda_function.action_performer.arn
  batch_size                         = 100
  maximum_batching_window_in_seconds = 30
}

resource "aws_lambda_event_source_mapping" "reactions_queue_to_reactioner" {
  event_source_arn                   = aws_sqs_queue.reactions_queue.arn
  function_name                      = aws_lambda_function.reactioner.arn
  batch_size                         = 100
  maximum_batching_window_in_seconds = 30
}
