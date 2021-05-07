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

# HMA Root/Main API Lambda

resource "aws_lambda_function" "api_root" {
  function_name = "${var.prefix}_api_root"
  package_type  = "Image"
  role          = aws_iam_role.api_root.arn
  image_uri     = var.lambda_docker_info.uri
  image_config {
    command = [var.lambda_docker_info.commands.api_root]
  }
  timeout     = 300
  memory_size = 512
  environment {
    variables = {
      DYNAMODB_TABLE                        = var.datastore.name
      HMA_CONFIG_TABLE                      = var.config_table.name
      IMAGE_BUCKET_NAME                     = var.image_data_storage.bucket_name
      IMAGE_FOLDER_KEY                      = var.image_data_storage.image_folder_key
      THREAT_EXCHANGE_DATA_BUCKET_NAME      = var.threat_exchange_data.bucket_name
      THREAT_EXCHANGE_DATA_FOLDER           = var.threat_exchange_data.data_folder
      THREAT_EXCHANGE_PDQ_FILE_EXTENSION    = var.threat_exchange_data.pdq_file_extension
      THREAT_EXCHANGE_API_TOKEN_SECRET_NAME = var.te_api_token_secret.name
      MEASURE_PERFORMANCE                   = var.measure_performance ? "True" : "False"
    }
  }
  tags = merge(
    var.additional_tags,
    {
      Name = "RootAPIFunction"
    }
  )
}

resource "aws_cloudwatch_log_group" "api_root" {
  name              = "/aws/lambda/${aws_lambda_function.api_root.function_name}"
  retention_in_days = var.log_retention_in_days
  tags = merge(
    var.additional_tags,
    {
      Name = "RootAPILambdaLogGroup"
    }
  )
}

resource "aws_iam_role" "api_root" {
  name_prefix        = "${var.prefix}_api_root"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags = merge(
    var.additional_tags,
    {
      Name = "RootAPILambdaRole"
    }
  )
}

data "aws_iam_policy_document" "api_root" {
  statement {
    effect    = "Allow"
    actions   = ["dynamodb:GetItem", "dynamodb:Query", "dynamodb:Scan", "dynamodb:UpdateItem"]
    resources = ["${var.datastore.arn}*"]
  }
  statement {
    effect    = "Allow"
    actions   = ["dynamodb:GetItem", "dynamodb:Query", "dynamodb:Scan", "dynamodb:PutItem", "dynamodb:DeleteItem"]
    resources = [var.config_table.arn]
  }
  statement {
    effect    = "Allow"
    actions   = ["s3:GetObject", "s3:PutObject"]
    resources = ["arn:aws:s3:::${var.image_data_storage.bucket_name}/${var.image_data_storage.image_folder_key}*"]
  }
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
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]
    resources = ["${aws_cloudwatch_log_group.api_root.arn}:*"]
  }
  
  statement {
    effect    = "Allow"
    actions   = ["cloudwatch:GetMetricStatistics"]
    resources = ["*"]
  }

  statement {
    effect    = "Allow"
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [var.te_api_token_secret.arn]
  }
}

resource "aws_iam_policy" "api_root" {
  name_prefix = "${var.prefix}_api_root_role_policy"
  description = "Permissions for Root API Lambda"
  policy      = data.aws_iam_policy_document.api_root.json
}

resource "aws_iam_role_policy_attachment" "api_root" {
  role       = aws_iam_role.api_root.name
  policy_arn = aws_iam_policy.api_root.arn
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

resource "aws_apigatewayv2_route" "hma_apigateway_get" {
  api_id             = aws_apigatewayv2_api.hma_apigateway.id
  route_key          = "GET /{proxy+}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.hma_apigateway.id
  target             = "integrations/${aws_apigatewayv2_integration.hma_apigateway.id}"
}

resource "aws_apigatewayv2_route" "hma_apigateway_post" {
  api_id             = aws_apigatewayv2_api.hma_apigateway.id
  route_key          = "POST /{proxy+}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.hma_apigateway.id
  target             = "integrations/${aws_apigatewayv2_integration.hma_apigateway.id}"
}

resource "aws_apigatewayv2_integration" "hma_apigateway" {
  api_id                 = aws_apigatewayv2_api.hma_apigateway.id
  credentials_arn        = aws_iam_role.hma_apigateway.arn
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"
  integration_uri        = aws_lambda_function.api_root.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_authorizer" "hma_apigateway" {
  api_id           = aws_apigatewayv2_api.hma_apigateway.id
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]
  name             = "${var.prefix}-jwt-authorizer"

  jwt_configuration {
    audience = [var.api_authorizer_audience]
    issuer   = var.api_authorizer_jwt_issuer
  }
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
    resources = [aws_lambda_function.api_root.arn]
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
