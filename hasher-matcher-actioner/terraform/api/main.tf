# Copyright (c) Meta Platforms, Inc. and affiliates.


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

data "aws_caller_identity" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
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
      SECRETS_PREFIX                        = var.secrets_prefix
      DYNAMODB_TABLE                        = var.datastore.name
      HMA_CONFIG_TABLE                      = var.config_table.name
      BANKS_TABLE                           = var.banks_datastore.name
      COUNTS_TABLE_NAME                     = var.counts_datastore.name
      IMAGE_BUCKET_NAME                     = var.image_data_storage.bucket_name
      IMAGE_PREFIX                          = var.image_data_storage.image_prefix
      THREAT_EXCHANGE_DATA_BUCKET_NAME      = var.threat_exchange_data.bucket_name
      THREAT_EXCHANGE_DATA_FOLDER           = var.threat_exchange_data.data_folder
      INDEXES_BUCKET_NAME                   = var.index_data_storage.bucket_name
      THREAT_EXCHANGE_API_TOKEN_SECRET_NAME = var.te_api_token_secret.name
      MEASURE_PERFORMANCE                   = var.measure_performance ? "True" : "False"
      WRITEBACKS_QUEUE_URL                  = var.writebacks_queue.url
      SUBMISSIONS_QUEUE_URL                 = var.submissions_queue.url
      HASHES_QUEUE_URL                      = var.hashes_queue.url
      BANKS_MEDIA_BUCKET_NAME               = var.banks_media_storage.bucket_name
      INDEXER_FUNCTION_NAME                 = var.indexer_function_name
      LCC_DURABLE_FS_PATH                   = "TODO: GET actual path. Verify API works with EFS security groups."
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
    actions   = ["dynamodb:GetItem", "dynamodb:Query", "dynamodb:Scan", "dynamodb:PutItem", "dynamodb:UpdateItem"]
    resources = ["${var.datastore.arn}*"]
  }
  statement {
    effect    = "Allow"
    actions   = ["dynamodb:GetItem", "dynamodb:Query", "dynamodb:Scan", "dynamodb:PutItem", "dynamodb:UpdateItem"]
    resources = ["${var.banks_datastore.arn}*"]
  }
  statement {
    effect    = "Allow"
    actions   = ["dynamodb:GetItem", "dynamodb:Query", "dynamodb:Scan"]
    resources = ["${var.counts_datastore.arn}*"]
  }
  statement {
    effect    = "Allow"
    actions   = ["dynamodb:GetItem", "dynamodb:Query", "dynamodb:Scan", "dynamodb:PutItem", "dynamodb:DeleteItem"]
    resources = [var.config_table.arn]
  }
  statement {
    effect  = "Allow"
    actions = ["s3:GetObject", "s3:PutObject"]
    resources = [
      "arn:aws:s3:::${var.image_data_storage.bucket_name}/${var.image_data_storage.image_prefix}*",
      "arn:aws:s3:::${var.index_data_storage.bucket_name}/${var.index_data_storage.index_folder_key}*",
      "arn:aws:s3:::${var.banks_media_storage.bucket_name}/*"
    ]
  }
  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject",
    ]
    resources = concat(
      [
        "arn:aws:s3:::${var.threat_exchange_data.bucket_name}/${var.threat_exchange_data.data_folder}*",
      ],
      [for partner_bucket in var.partner_image_buckets : "${partner_bucket.arn}/*"]
    )
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
    effect  = "Allow"
    actions = ["secretsmanager:GetSecretValue", "secretsmanager:CreateSecret", "secretsmanager:PutSecretValue"]
    resources = [
      var.te_api_token_secret.arn,
      "arn:aws:secretsmanager:${data.aws_region.current.name}:${local.account_id}:secret:${var.secrets_prefix}*"
    ]
  }
  statement {
    effect    = "Allow"
    actions   = ["sqs:SendMessage"]
    resources = [var.writebacks_queue.arn, var.submissions_queue.arn, var.hashes_queue.arn]
  }

  statement {
    effect    = "Allow"
    actions   = ["lambda:GetFunctionConfiguration"]
    resources = [aws_lambda_function.api_root.arn]
  }

  statement {
    effect    = "Allow"
    actions   = ["lambda:InvokeAsync", "lambda:InvokeFunction"]
    resources = [var.indexer_function_arn]
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

# Authorizer API Lambda

locals {
  user_pool_url = "https://cognito-idp.${data.aws_region.current.name}.amazonaws.com/${var.api_and_webapp_user_pool_id}"
}

resource "aws_lambda_function" "api_auth" {
  function_name = "${var.prefix}_api_auth"
  package_type  = "Image"
  role          = aws_iam_role.api_auth.arn
  image_uri     = var.lambda_docker_info.uri
  image_config {
    command = [var.lambda_docker_info.commands.api_auth]
  }
  timeout     = 30
  memory_size = 128
  environment {
    variables = {
      SECRETS_PREFIX               = var.secrets_prefix
      HMA_ACCESS_TOKEN_SECRET_NAME = var.hma_api_access_tokens_secret.name
      USER_POOL_URL                = local.user_pool_url
      CLIENT_ID                    = var.api_authorizer_audience
    }
  }
  tags = merge(
    var.additional_tags,
    {
      Name = "AuthAPIFunction"
    }
  )
}

resource "aws_cloudwatch_log_group" "api_auth" {
  name              = "/aws/lambda/${aws_lambda_function.api_auth.function_name}"
  retention_in_days = var.log_retention_in_days
  tags = merge(
    var.additional_tags,
    {
      Name = "AuthAPILambdaLogGroup"
    }
  )
}

resource "aws_iam_role" "api_auth" {
  name_prefix        = "${var.prefix}_api_auth"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags = merge(
    var.additional_tags,
    {
      Name = "AuthAPILambdaRole"
    }
  )
}

data "aws_iam_policy_document" "api_auth" {
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]
    resources = ["${aws_cloudwatch_log_group.api_auth.arn}:*"]
  }
  statement {
    effect    = "Allow"
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [var.hma_api_access_tokens_secret.arn]
  }
}

resource "aws_iam_policy" "api_auth" {
  name_prefix = "${var.prefix}_api_auth_role_policy"
  description = "Permissions for Auth API Lambda"
  policy      = data.aws_iam_policy_document.api_auth.json
}

resource "aws_iam_role_policy_attachment" "api_auth" {
  role       = aws_iam_role.api_auth.name
  policy_arn = aws_iam_policy.api_auth.arn
}

# API Gateway

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

resource "aws_api_gateway_rest_api" "hma_api_gw" {
  name = "${var.prefix}_hma_api_gw"
  endpoint_configuration {
    types            = var.api_in_vpc ? ["PRIVATE"] : ["REGIONAL"]
    vpc_endpoint_ids = length(aws_vpc_endpoint.vpce) > 0 ? aws_vpc_endpoint.vpce[*].id : null
  }
  policy             = length(data.aws_iam_policy_document.hma_api_gw_in_vpc) > 0 ? data.aws_iam_policy_document.hma_api_gw_in_vpc[0].json : null
  binary_media_types = ["*/*"]
}

resource "aws_api_gateway_resource" "hma_api_gw" {
  parent_id   = aws_api_gateway_rest_api.hma_api_gw.root_resource_id
  path_part   = "{proxy+}"
  rest_api_id = aws_api_gateway_rest_api.hma_api_gw.id
}

resource "aws_api_gateway_method" "hma_api_gw" {
  authorization = "CUSTOM"
  http_method   = "ANY"
  authorizer_id = aws_api_gateway_authorizer.hma_api_gw.id
  resource_id   = aws_api_gateway_resource.hma_api_gw.id
  rest_api_id   = aws_api_gateway_rest_api.hma_api_gw.id
}

resource "aws_api_gateway_authorizer" "hma_api_gw" {
  rest_api_id            = aws_api_gateway_rest_api.hma_api_gw.id
  type                   = "REQUEST"
  authorizer_credentials = aws_iam_role.hma_api_gw.arn
  authorizer_uri         = aws_lambda_function.api_auth.invoke_arn
  name                   = "${aws_api_gateway_rest_api.hma_api_gw.name}_authorizer"
  identity_source        = "method.request.header.Authorization"
}

resource "aws_api_gateway_integration" "hma_api_gw" {
  http_method             = aws_api_gateway_method.hma_api_gw.http_method
  resource_id             = aws_api_gateway_resource.hma_api_gw.id
  rest_api_id             = aws_api_gateway_rest_api.hma_api_gw.id
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.api_root.invoke_arn
}

resource "aws_api_gateway_deployment" "hma_api_gw" {
  depends_on = [
    aws_vpc_endpoint.vpce
  ]
  rest_api_id = aws_api_gateway_rest_api.hma_api_gw.id
  triggers = {
    redeployment = sha1(jsonencode([
      var.lambda_docker_info.uri,
      aws_api_gateway_resource.hma_api_gw.id,
      aws_api_gateway_method.hma_api_gw.id,
      aws_api_gateway_integration.hma_api_gw.id,
      aws_lambda_function.api_auth.id,
      aws_lambda_function.api_root.id,
      "${sha1(file("${path.module}/main.tf"))}"
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "hma_api_gw" {
  deployment_id = aws_api_gateway_deployment.hma_api_gw.id
  rest_api_id   = aws_api_gateway_rest_api.hma_api_gw.id
  stage_name    = "api"
}

resource "aws_iam_role" "hma_api_gw" {
  name_prefix        = "${var.prefix}_hma_api_gw"
  assume_role_policy = data.aws_iam_policy_document.apigateway_assume_role.json
  tags = merge(
    var.additional_tags,
    {
      Name = "HMAAPIGatewayRole"
    }
  )
}

data "aws_iam_policy_document" "hma_api_gw" {
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]
    resources = ["${aws_cloudwatch_log_group.hma_api_gw.arn}:*"]
  }
  statement {
    effect    = "Allow"
    actions   = ["lambda:InvokeFunction", ]
    resources = ["${aws_lambda_function.api_root.arn}:*", aws_lambda_function.api_auth.arn]
  }
}

resource "aws_iam_policy" "hma_api_gw" {
  name_prefix = "${var.prefix}_hma_api_gw_role_policy"
  description = "Permissions for HMA Rest API Gateway"
  policy      = data.aws_iam_policy_document.hma_api_gw.json
}

resource "aws_iam_role_policy_attachment" "hma_api_gw" {
  role       = aws_iam_role.hma_api_gw.name
  policy_arn = aws_iam_policy.hma_api_gw.arn
}

resource "aws_cloudwatch_log_group" "hma_api_gw" {
  name              = "/aws/apigateway/${aws_api_gateway_rest_api.hma_api_gw.name}"
  retention_in_days = var.log_retention_in_days
  tags = merge(
    var.additional_tags,
    {
      Name = "HMAAPIGatewayLogGroup"
    }
  )
}

resource "aws_lambda_permission" "apigw_lambda" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api_root.function_name
  principal     = "apigateway.amazonaws.com"

  # More: http://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-control-access-using-iam-policies-to-invoke-api.html
  source_arn = "arn:aws:execute-api:${data.aws_region.current.name}:${local.account_id}:${aws_api_gateway_rest_api.hma_api_gw.id}/*/${aws_api_gateway_method.hma_api_gw.http_method}${aws_api_gateway_resource.hma_api_gw.path}"
}

resource "aws_api_gateway_method" "cors" {
  rest_api_id   = aws_api_gateway_rest_api.hma_api_gw.id
  resource_id   = aws_api_gateway_resource.hma_api_gw.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "cors" {
  rest_api_id = aws_api_gateway_rest_api.hma_api_gw.id
  resource_id = aws_api_gateway_resource.hma_api_gw.id
  http_method = aws_api_gateway_method.cors.http_method
  type        = "MOCK"
  request_templates = {
    "application/json" : "{\"statusCode\": 200}"
  }
  content_handling = "CONVERT_TO_TEXT"
}

resource "aws_api_gateway_method_response" "cors" {
  depends_on  = [aws_api_gateway_method.cors]
  rest_api_id = aws_api_gateway_rest_api.hma_api_gw.id
  resource_id = aws_api_gateway_resource.hma_api_gw.id
  http_method = aws_api_gateway_method.cors.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true,
    "method.response.header.Access-Control-Allow-Methods" = true,
    "method.response.header.Access-Control-Allow-Headers" = true
  }
  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "cors" {
  depends_on  = [aws_api_gateway_integration.cors, aws_api_gateway_method_response.cors]
  rest_api_id = aws_api_gateway_rest_api.hma_api_gw.id
  resource_id = aws_api_gateway_resource.hma_api_gw.id
  http_method = aws_api_gateway_method.cors.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = "'*'",
    "method.response.header.Access-Control-Allow-Headers" = "'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token, Authorization'",
    "method.response.header.Access-Control-Allow-Methods" = "'GET, POST, PUT, DELETE, OPTIONS'", # remove or add methods as needed
  }
}

# VPC additions
data "aws_vpc_endpoint_service" "vpc_service" {
  service = "execute-api"
}

resource "aws_vpc_endpoint" "vpce" {
  count               = var.api_in_vpc ? 1 : 0
  vpc_id              = var.vpc_id
  service_name        = data.aws_vpc_endpoint_service.vpc_service.service_name
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true

  subnet_ids         = var.vpc_subnets
  security_group_ids = var.security_groups
}

resource "aws_api_gateway_rest_api_policy" "hma_api_gw" {
  count       = var.api_in_vpc ? 1 : 0
  rest_api_id = aws_api_gateway_rest_api.hma_api_gw.id
  policy      = data.aws_iam_policy_document.hma_api_gw_in_vpc[0].json
}
data "aws_iam_policy_document" "hma_api_gw_in_vpc" {
  count = var.api_in_vpc ? 1 : 0

  statement {
    effect    = "Allow"
    actions   = ["execute-api:Invoke"]
    resources = ["*"]
    condition {
      test     = "StringEquals"
      variable = "aws:SourceVpce"
      values   = [aws_vpc_endpoint.vpce[count.index].id]
    }
    principals {
      type        = "*"
      identifiers = ["*"]
    }
  }
  statement {
    effect    = "Deny"
    actions   = ["execute-api:Invoke"]
    resources = ["*"]
    condition {
      test     = "StringNotEquals"
      variable = "aws:SourceVpce"
      values   = [aws_vpc_endpoint.vpce[count.index].id]
    }
    principals {
      type        = "*"
      identifiers = ["*"]
    }
  }
}

# Connect partner s3 buckets to api_root 

resource "aws_lambda_permission" "allow_bucket" {
  count = var.enable_partner_upload_notification ? length(var.partner_image_buckets) : 0

  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api_root.arn
  principal     = "s3.amazonaws.com"
  source_arn    = var.partner_image_buckets[count.index].arn
}

resource "aws_s3_bucket_notification" "bucket_notification" {
  count = var.enable_partner_upload_notification ? length(var.partner_image_buckets) : 0

  bucket = var.partner_image_buckets[count.index].name

  lambda_function {
    lambda_function_arn = aws_lambda_function.api_root.arn
    events              = ["s3:ObjectCreated:*"]

    # Check if a prefix filter (or the aliases folder, path) was specified
    # Otherwise no prefix constraint
    filter_prefix = lookup(var.partner_image_buckets[count.index].params, "prefix",
      lookup(var.partner_image_buckets[count.index].params, "folder",
        lookup(var.partner_image_buckets[count.index].params, "path", "")
      )
    )

    # Check if a suffix filter (or the alias extension) was specified
    # Otherwise no suffix constraint
    filter_suffix = lookup(var.partner_image_buckets[count.index].params, "suffix",
      lookup(var.partner_image_buckets[count.index].params, "extension", "")
    )
  }

  depends_on = [aws_lambda_permission.allow_bucket]
}
