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

# S3 Bucket

resource "aws_s3_bucket" "data_bucket" {
  bucket_prefix = "${var.prefix}-hashing-data"
  acl           = "private"
  tags = merge(
    var.additional_tags,
    {
      Name = "HashingDataBucket"
    }
  )
  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["PUT"]
    allowed_origins = ["*"]
    max_age_seconds = 3000
  }

  versioning {
    enabled = true
  }
  # For development, this makes cleanup easier
  # If deploying for real, this should not be used
  # Could also be set with a variable
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "data_bucket" {
  bucket = aws_s3_bucket.data_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_notification" "bucket_notifications" {
  bucket = aws_s3_bucket.data_bucket.id

  topic {
    topic_arn     = aws_sns_topic.image_notification_topic.arn
    events        = ["s3:ObjectCreated:*"]
    filter_prefix = "images/"
  }

  topic {
    topic_arn     = aws_sns_topic.threat_exchange_data.arn
    events        = ["s3:ObjectCreated:*"]
    filter_prefix = "threat_exchange_data/"
  }
}


# Connect local s3 buckets to bucket_hasher

resource "aws_lambda_function" "bucket_hasher" {
  function_name = "${var.prefix}_bucket_hasher"
  package_type  = "Image"
  role          = aws_iam_role.bucket_hasher.arn
  image_uri     = var.lambda_docker_info.uri

  image_config {
    command = [var.lambda_docker_info.commands.bucket_hasher]
  }

  timeout     = 300
  memory_size = 512
}

resource "aws_iam_role" "bucket_hasher" {
  name_prefix        = "${var.prefix}_bucket_hasher"
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

resource "aws_iam_policy" "bucket_hasher" {
  name_prefix = "${var.prefix}_bucket_hasher_role_policy"
  description = "Permissions for Bucket Hasher Lambda"
  policy      = data.aws_iam_policy_document.bucket_hasher.json
}

resource "aws_iam_role_policy_attachment" "pdq_hasher" {
  role       = aws_iam_role.bucket_hasher.name
  policy_arn = aws_iam_policy.bucket_hasher.arn
}

data "aws_iam_policy_document" "bucket_hasher" {

  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]
    resources = ["${aws_cloudwatch_log_group.bucket_hasher.arn}:*"]
  }
  statement {
    effect    = "Allow"
    actions   = ["cloudwatch:PutMetricData"]
    resources = ["*"]
  }
}

resource "aws_cloudwatch_log_group" "bucket_hasher" {
  name              = "/aws/lambda/${aws_lambda_function.bucket_hasher.function_name}"
  retention_in_days = var.log_retention_in_days

  tags = merge(
    var.additional_tags,
    {
      Name = "BucketHasherLambdaLogGroup"
    }
  )
}

resource "aws_lambda_permission" "allow_bucket" {
  count = length(var.local_image_buckets)

  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.bucket_hasher.arn
  principal     = "s3.amazonaws.com"
  source_arn    = var.local_image_buckets[count.index].arn
}

resource "aws_s3_bucket_notification" "bucket_notification" {
  count = length(var.local_image_buckets)

  bucket = var.local_image_buckets[count.index].name

  lambda_function {
    lambda_function_arn = aws_lambda_function.bucket_hasher.arn
    events              = ["s3:ObjectCreated:*"]

    # TODO: Allow filtering to enable hashing to only certain f
    # olders and file types. eg...
    #
    # filter_prefix       = "images/"
    # filter_suffix       = ".jpg"
  }

  depends_on = [aws_lambda_permission.allow_bucket]
}


# ThreatExchange Data File Folder

resource "aws_s3_bucket_object" "threat_exchange_data" {
  bucket       = aws_s3_bucket.data_bucket.id
  key          = "threat_exchange_data/"
  content_type = "application/x-directory"
  tags = merge(
    var.additional_tags,
    {
      Name = "ThreatExchangeDataFolder"
    }
  )
}

resource "aws_sns_topic" "threat_exchange_data" {
  name_prefix = "${var.prefix}-threatexchange-data"
  tags = merge(
    var.additional_tags,
    {
      Name = "ThreatExchangeDataFolderUpdated"
    }
  )
}

data "aws_iam_policy_document" "threat_exchange_data" {
  statement {
    effect    = "Allow"
    actions   = ["SNS:Publish"]
    resources = [aws_sns_topic.threat_exchange_data.arn]
    principals {
      type        = "Service"
      identifiers = ["s3.amazonaws.com"]
    }
    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = [aws_s3_bucket.data_bucket.arn]
    }
  }
}

resource "aws_sns_topic_policy" "threat_exchange_data" {
  arn    = aws_sns_topic.threat_exchange_data.arn
  policy = data.aws_iam_policy_document.threat_exchange_data.json
}


# Index File Folder

resource "aws_s3_bucket_object" "index" {
  bucket       = aws_s3_bucket.data_bucket.id
  key          = "index/"
  content_type = "application/x-directory"
  tags = merge(
    var.additional_tags,
    {
      Name = "IndexesFolder"
    }
  )
}

# Image File Notifications

resource "aws_s3_bucket_object" "images" {
  bucket       = aws_s3_bucket.data_bucket.id
  key          = "images/"
  content_type = "application/x-directory"
  tags = merge(
    var.additional_tags,
    {
      Name = "ImagesContentFolder"
    }
  )
}

resource "aws_sns_topic" "image_notification_topic" {
  name_prefix = "${var.prefix}-images"
  tags = merge(
    var.additional_tags,
    {
      Name = "ImagesContentFolderUpdated"
    }
  )
}

data "aws_iam_policy_document" "image_notification_topic_policy" {
  statement {
    effect    = "Allow"
    actions   = ["SNS:Publish"]
    resources = [aws_sns_topic.image_notification_topic.arn]
    principals {
      type        = "Service"
      identifiers = ["s3.amazonaws.com"]
    }
    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = [aws_s3_bucket.data_bucket.arn]
    }
  }
}

resource "aws_sns_topic_policy" "image_notification_topic_policy" {
  arn = aws_sns_topic.image_notification_topic.arn

  policy = data.aws_iam_policy_document.image_notification_topic_policy.json
}

