# Copyright (c) Meta Platforms, Inc. and affiliates.

### Lambda for custodian ###
data "aws_region" "current" {}
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

resource "aws_lambda_function" "custodian" {
  function_name = "${var.prefix}_custodian"
  package_type  = "Image"
  role          = aws_iam_role.custodian.arn
  image_uri     = var.lambda_docker_info.uri
  image_config {
    command = ["hmalib.lambdas.custodian.lambda_handler"]
  }

  timeout = 60 * 12

  memory_size = 128
}

resource "aws_cloudwatch_event_target" "custodian" {
  arn  = aws_lambda_function.custodian.arn
  rule = aws_cloudwatch_event_rule.recurring_custodian.name
}
resource "aws_cloudwatch_event_rule" "recurring_custodian" {
  name                = "${var.prefix}RecurringSquashUpdate"
  description         = "Squash content based on a timely interval"
  schedule_expression = "rate(${var.custodian_frequency})"
  role_arn            = aws_iam_role.custodian_trigger.arn
}

resource "aws_iam_role" "custodian_trigger" {
  name_prefix        = "${var.prefix}_custodian_trigger"
  assume_role_policy = data.aws_iam_policy_document.custodian_trigger_assume_role.json

  tags = merge(
    var.additional_tags,
    {
      Name = "CustodianLambdaTriggerRole"
    }
  )
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "${var.prefix}AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.custodian.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.custodian_trigger.arn
}

resource "aws_cloudwatch_event_rule" "custodian_trigger" {
  name                = "${var.prefix}-RecurringIndexBuild"
  description         = "Rebuild Index on a regular cadence"
  schedule_expression = "rate(${var.custodian_frequency})"
  role_arn            = aws_iam_role.custodian_trigger.arn
}


data "aws_iam_policy_document" "custodian_trigger_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }
  }
}


resource "aws_cloudwatch_log_group" "custodian" {
  name = "/aws/lambda/${aws_lambda_function.custodian.function_name}"
  tags = merge(
    var.additional_tags,
    {
      Name = "CustodianLambdaLogGroup"
    }
  )
}

resource "aws_iam_role" "custodian" {
  name_prefix        = "${var.prefix}_custodian"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags = merge(
    var.additional_tags,
    {
      Name = "CustodianLambdaRole"
    }
  )
}

data "aws_iam_policy_document" "custodian" {

  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]
    resources = ["${aws_cloudwatch_log_group.custodian.arn}:*"]
  }

}


locals {

  stacked_graph = jsonencode({
    height = 6,
    width  = 6,
    type   = "metric",
    properties = {
      view    = "timeSeries",
      stacked = true,
      metrics = [
        ["ThreatExchange/HMA", "lcc.get_data-duration"],
        [".", "lcc.in_memory_processing-duration"],
        [".", "lcc.build_index-duration"]
      ],
      region = "${data.aws_region.current.name}"
    }
  })

  line_graph = jsonencode({
    width  = 6
    height = 6
    type   = "metric"
    properties = {
      view    = "timeSeries"
      stacked = false
      metrics = [["ThreatExchange/HMA", "lcc.build_index-count"]
      ]
      region = "${data.aws_region.current.name}"
    }
  })

  dashboard_body = <<JSON
  {
    "widgets": [
      ${local.stacked_graph},
      ${local.line_graph}
      ]
  }
  JSON
}


resource "aws_cloudwatch_dashboard" "basic_dashboard" {
  dashboard_name = "${var.prefix}-lcc-dashboard"
  dashboard_body = replace(local.dashboard_body, "/\"([0-9]+)\"/", "$1")
}

resource "aws_iam_policy" "custodian" {
  name_prefix = "${var.prefix}_custodian_role_policy"
  description = "Permissions for custodian Lambda"
  policy      = data.aws_iam_policy_document.custodian.json
}

resource "aws_iam_role_policy_attachment" "custodian" {
  role       = aws_iam_role.custodian.name
  policy_arn = aws_iam_policy.custodian.arn
}
