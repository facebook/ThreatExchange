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
resource "null_resource" "provide_sample_pdq_data_holidays" {
  # To force-update on existing deployment, taint and apply terraform again
  # $ terraform taint module.hashing_data.null_resource.provide_sample_pdq_data_holidays
  # $ terraform apply

  # To get a sensible privacy group value, we reverse engineer the filename split at
  # hmalib.common.s3_adapters.ThreatExchangeS3Adapter._parse_file at line 118
  depends_on = [
    aws_s3_bucket_object.threat_exchange_data
  ]

  provisioner "local-exec" {
    environment = {
      PRIVACY_GROUP = "inria-holidays-test"
    }

    command = "aws s3 cp ../sample_data/holidays-jpg1-pdq-hashes.csv s3://${aws_s3_bucket_object.threat_exchange_data.bucket}/${aws_s3_bucket_object.threat_exchange_data.key}$PRIVACY_GROUP.holidays-jpg1-pdq-hashes.pdq.te"
  }
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

# DynamoDB Datastore

resource "aws_dynamodb_table" "datastore" {
  name         = "${var.prefix}-HMADataStore"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "PK"
  range_key    = "SK"
  attribute {
    name = "PK"
    type = "S"
  }
  attribute {
    name = "SK"
    type = "S"
  }
  attribute {
    name = "GSI1-PK"
    type = "S"
  }
  attribute {
    name = "GSI1-SK"
    type = "S"
  }
  attribute {
    name = "GSI2-PK"
    type = "S"
  }
  attribute {
    name = "UpdatedAt"
    type = "S"
  }

  global_secondary_index {
    name            = "GSI-1"
    hash_key        = "GSI1-PK"
    range_key       = "GSI1-SK"
    projection_type = "INCLUDE"
    non_key_attributes = [
      "ContentHash",
      "UpdatedAt",
      "SignalHash",
      "SignalSource",
      "HashType",
      "Labels"
    ]
  }

  global_secondary_index {
    name            = "GSI-2"
    hash_key        = "GSI2-PK"
    range_key       = "UpdatedAt"
    projection_type = "INCLUDE"
    non_key_attributes = [
      "ContentHash",
      "SignalHash",
      "SignalSource",
      "HashType",
      "Labels"
    ]
  }

  tags = merge(
    var.additional_tags,
    {
      Name = "HMADataStore"
    }
  )
}
