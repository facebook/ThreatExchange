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

# create hasher_integrations lambda fucntion. This function can recieve aws events 
# from different sources and enque them to the hasher. Currently, the only supported
# is upload to a specified s3 bucket


resource "aws_lambda_function" "hasher_integrations" {
  function_name = "${var.prefix}_hasher_integrations"
  package_type  = "Image"
  role          = aws_iam_role.hasher_integrations.arn
  image_uri     = var.lambda_docker_info.uri

  image_config {
    command = [var.lambda_docker_info.commands.hasher_integrations]
  }

  timeout     = 300
  memory_size = 512

}

resource "aws_iam_role" "hasher_integrations" {
  name_prefix        = "${var.prefix}_hasher_integrations"
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

resource "aws_iam_policy" "hasher_integrations" {
  name_prefix = "${var.prefix}_hasher_integrations_role_policy"
  description = "Permissions for Hasher Integrations Lambda"
  policy      = data.aws_iam_policy_document.hasher_integrations.json
}

resource "aws_iam_role_policy_attachment" "hasher_integrations" {
  role       = aws_iam_role.hasher_integrations.name
  policy_arn = aws_iam_policy.hasher_integrations.arn
}

data "aws_iam_policy_document" "hasher_integrations" {

  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]
    resources = ["${aws_cloudwatch_log_group.hasher_integrations.arn}:*"]
  }
  statement {
    effect    = "Allow"
    actions   = ["cloudwatch:PutMetricData"]
    resources = ["*"]
  }
}

resource "aws_cloudwatch_log_group" "hasher_integrations" {
  name              = "/aws/lambda/${aws_lambda_function.hasher_integrations.function_name}"
  retention_in_days = var.log_retention_in_days

  tags = merge(
    var.additional_tags,
    {
      Name = "HasherIntegrationsLambdaLogGroup"
    }
  )
}

# Connect local s3 buckets to hasher_integration 

resource "aws_lambda_permission" "allow_bucket" {
  count = length(var.local_image_buckets)

  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.hasher_integrations.arn
  principal     = "s3.amazonaws.com"
  source_arn    = var.local_image_buckets[count.index].arn
}

resource "aws_s3_bucket_notification" "bucket_notification" {
  count = length(var.local_image_buckets)

  bucket = var.local_image_buckets[count.index].name

  lambda_function {
    lambda_function_arn = aws_lambda_function.hasher_integrations.arn
    events              = ["s3:ObjectCreated:*"]

    # TODO: Allow filtering to enable hashing to only certain f
    # olders and file types. eg...
    #
    # filter_prefix       = "images/"
    # filter_suffix       = ".jpg"
  }

  depends_on = [aws_lambda_permission.allow_bucket]
}