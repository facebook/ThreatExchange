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

# create local_bucket_hasher lambda fucntion. This function can recieve aws events 
# from different sources and enque them to the hasher. Currently, the only supported
# is upload to a specified s3 bucket


resource "aws_lambda_function" "local_bucket_hasher" {
  function_name = "${var.prefix}_local_bucket_hasher"
  package_type  = "Image"
  role          = aws_iam_role.local_bucket_hasher.arn
  image_uri     = var.lambda_docker_info.uri

  image_config {
    command = [var.lambda_docker_info.commands.local_bucket_hasher]
  }

  timeout     = 300
  memory_size = 512

  environment {
    variables = {
      PDQ_IMAGES_QUEUE_URL = var.pdq_images_queue.id
    }
  }

}

resource "aws_iam_role" "local_bucket_hasher" {
  name_prefix        = "${var.prefix}_local_bucket_hasher"
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

resource "aws_iam_policy" "local_bucket_hasher" {
  name_prefix = "${var.prefix}_local_bucket_hasher_role_policy"
  description = "Permissions for Local Bucket Hasher Lambda"
  policy      = data.aws_iam_policy_document.local_bucket_hasher.json
}

resource "aws_iam_role_policy_attachment" "local_bucket_hasher" {
  role       = aws_iam_role.local_bucket_hasher.name
  policy_arn = aws_iam_policy.local_bucket_hasher.arn
}

data "aws_iam_policy_document" "local_bucket_hasher" {

  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]
    resources = ["${aws_cloudwatch_log_group.local_bucket_hasher.arn}:*"]
  }
  statement {
    effect    = "Allow"
    actions   = ["cloudwatch:PutMetricData"]
    resources = ["*"]
  }

  statement {
    effect    = "Allow"
    actions   = ["sqs:SendMessage"]
    resources = [var.pdq_images_queue.arn]
  }

  statement {
    effect = "Allow"
    actions = [
      "dynamodb:Get*",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem"
    ]
    resources = [var.datastore.arn]
  }

  statement {
    effect = "Allow"
    actions = [
      "SNS:Publish"
    ]
    resources = [var.images_topic_arn]
  }

  
}

resource "aws_cloudwatch_log_group" "local_bucket_hasher" {
  name              = "/aws/lambda/${aws_lambda_function.local_bucket_hasher.function_name}"
  retention_in_days = var.log_retention_in_days

  tags = merge(
    var.additional_tags,
    {
      Name = "LocalBucketHasherLambdaLogGroup"
    }
  )
}

# Connect local s3 buckets to local_bucket_hasher 

resource "aws_lambda_permission" "allow_bucket" {
  count = length(var.local_image_buckets)

  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.local_bucket_hasher.arn
  principal     = "s3.amazonaws.com"
  source_arn    = var.local_image_buckets[count.index].arn
}

resource "aws_s3_bucket_notification" "bucket_notification" {
  count = length(var.local_image_buckets)

  bucket = var.local_image_buckets[count.index].name

  lambda_function {
    lambda_function_arn = aws_lambda_function.local_bucket_hasher.arn
    events              = ["s3:ObjectCreated:*"]

    # TODO: Allow filtering to enable hashing to only certain f
    # olders and file types. eg...
    #
    # filter_prefix       = "images/"
    # filter_suffix       = ".jpg"
  }

  depends_on = [aws_lambda_permission.allow_bucket]
}