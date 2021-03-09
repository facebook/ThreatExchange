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

# HMA Status API Lambda

resource "aws_lambda_function" "status_api" {
  function_name = "${var.prefix}_status_api"
  package_type  = "Image"
  role          = aws_iam_role.status_api.arn
  image_uri     = var.lambda_docker_info.uri
  image_config {
    command = [var.lambda_docker_info.commands.status_api]
  }
  timeout     = 300
  memory_size = 512
  environment {
    variables = {
      DYNAMODB_TABLE = var.datastore.name
    }
  }
  tags = merge(
    var.additional_tags,
    {
      Name = "StatusAPIFunction"
    }
  )
}

resource "aws_cloudwatch_log_group" "status_api" {
  name              = "/aws/lambda/${aws_lambda_function.status_api.function_name}"
  retention_in_days = var.log_retention_in_days
  tags = merge(
    var.additional_tags,
    {
      Name = "StatusAPILambdaLogGroup"
    }
  )
}

resource "aws_iam_role" "status_api" {
  name_prefix        = "${var.prefix}_status_api"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags = merge(
    var.additional_tags,
    {
      Name = "StatusAPILambdaRole"
    }
  )
}

data "aws_iam_policy_document" "status_api" {
  statement {
    effect    = "Allow"
    actions   = ["dynamodb:GetItem"]
    resources = [var.datastore.arn]
  }
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]
    resources = ["${aws_cloudwatch_log_group.status_api.arn}:*"]
  }
}

resource "aws_iam_policy" "status_api" {
  name_prefix = "${var.prefix}_status_api_role_policy"
  description = "Permissions for Status API Lambda"
  policy      = data.aws_iam_policy_document.status_api.json
}

resource "aws_iam_role_policy_attachment" "status_api" {
  role       = aws_iam_role.status_api.name
  policy_arn = aws_iam_policy.status_api.arn
}

# API Gateway

resource "aws_apigatewayv2_api" "hma_apigateway" {
  name          = "${var.prefix}_hma_api"
  protocol_type = "HTTP"
  tags = merge(
    var.additional_tags,
    {
      Name = "HMAAPIGateway"
    }
  )
  cors_configuration {
    allow_headers = ["*"]
    allow_methods = ["*"]
    allow_origins = ["*"]
  }
}

resource "aws_apigatewayv2_stage" "hma_apigateway" {
  name        = "$default"
  api_id      = aws_apigatewayv2_api.hma_apigateway.id
  auto_deploy = true
  # TODO have enable/disable of access logs be configurable 
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.hma_apigateway.arn
    format          = "$context.identity.sourceIp - - [$context.requestTime] \"$context.httpMethod $context.routeKey $context.protocol\" $context.status $context.responseLength $context.requestId $context.integrationErrorMessage"
  }
}

resource "aws_apigatewayv2_route" "hma_apigateway" {
  api_id             = aws_apigatewayv2_api.hma_apigateway.id
  route_key          = "$default"
  authorization_type = "AWS_IAM"
  target             = "integrations/${aws_apigatewayv2_integration.hma_apigateway.id}"
}

resource "aws_apigatewayv2_integration" "hma_apigateway" {
  api_id             = aws_apigatewayv2_api.hma_apigateway.id
  credentials_arn    = aws_iam_role.hma_apigateway.arn
  integration_type   = "AWS_PROXY"
  integration_method = "POST"
  integration_uri    = aws_lambda_function.status_api.invoke_arn
}

resource "aws_cloudwatch_log_group" "hma_apigateway" {
  name              = "/aws/apigateway/${aws_apigatewayv2_api.hma_apigateway.name}"
  retention_in_days = var.log_retention_in_days
  tags = merge(
    var.additional_tags,
    {
      Name = "HMAAPIGatewayLogGroup"
    }
  )
}

# IAM Policy for Gateway

data "aws_iam_policy_document" "apigateway_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["apigateway.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "hma_apigateway" {
  name_prefix        = "${var.prefix}_hma_apigateway"
  assume_role_policy = data.aws_iam_policy_document.apigateway_assume_role.json
  tags = merge(
    var.additional_tags,
    {
      Name = "HMAAPIGatewayRole"
    }
  )
}

data "aws_iam_policy_document" "hma_apigateway" {
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]
    resources = ["${aws_cloudwatch_log_group.hma_apigateway.arn}:*"]
  }
  statement {
    effect    = "Allow"
    actions   = ["lambda:InvokeFunction", ]
    resources = [aws_lambda_function.status_api.arn]
  }
}

resource "aws_iam_policy" "hma_apigateway" {
  name_prefix = "${var.prefix}_hma_apigateway_role_policy"
  description = "Permissions for HMA API Gateway"
  policy      = data.aws_iam_policy_document.hma_apigateway.json
}

resource "aws_iam_role_policy_attachment" "hma_apigateway" {
  role       = aws_iam_role.hma_apigateway.name
  policy_arn = aws_iam_policy.hma_apigateway.arn
}
