# Copyright (c) Meta Platforms, Inc. and affiliates.

## Integrations Lambda - maybe move to its own module
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

resource "aws_lambda_function" "integrations" {
  function_name = "${var.prefix}_integrations"
  package_type  = "Image"
  role          = aws_iam_role.integrations.arn
  image_uri     = var.lambda_docker_info.uri
  image_config {
    command = [var.lambda_docker_info.commands.integrations]
  }
  timeout     = 300
  memory_size = 512
  # hard coded for now in lambda. Should eventually becoem terraform variables
  #environment {
  #variables = {
  #  API_TOKEN = var.api_token
  #  HMA_API_GATEWAY_URL  = var.api_url
  #  WORKPLACE_APP_SECRET = var.workplace_app_secret
  #}
  #}
  tags = {
    Name = "IntegrationsFunction"
  }
}

resource "aws_cloudwatch_log_group" "integrations" {
  name              = "/aws/lambda/${aws_lambda_function.integrations.function_name}"
  retention_in_days = var.log_retention_in_days
  tags = {
    Name = "IntegrationsLambdaLogGroup"
  }
}

resource "aws_iam_role" "integrations" {
  name_prefix        = "${var.prefix}_integrations"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags = {
    Name = "IntegrationsLambdaRole"
  }
}

data "aws_iam_policy_document" "integrations" {
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]
    resources = ["${aws_cloudwatch_log_group.integrations.arn}:*"]
  }

  statement {
    effect    = "Allow"
    actions   = ["cloudwatch:GetMetricStatistics"]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "integrations" {
  name_prefix = "${var.prefix}_api_root_role_policy"
  description = "Permissions for Integrations Lambda"
  policy      = data.aws_iam_policy_document.integrations.json
}

resource "aws_iam_role_policy_attachment" "integrations" {
  role       = aws_iam_role.integrations.name
  policy_arn = aws_iam_policy.integrations.arn
}
