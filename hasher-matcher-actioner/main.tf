# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "hashing_bucket" {
  acl = "private"
  versioning {
    enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "hashing_bucket" {
  bucket = aws_s3_bucket.hashing_bucket.id
   
  block_public_acls = true
  block_public_policy = true
  ignore_public_acls = true
  restrict_public_buckets = true
}

resource "aws_sns_topic" "hashing_bucket_notifications" {
  name_prefix = "${var.prefix}-hashing-bucket-"
}

resource "aws_sns_topic_policy" "hashing_bucket_notifications_policy" {

  arn = aws_sns_topic.hashing_bucket_notifications.arn

  policy = <<END_OF_POLICY
{
  "Version": "2012-10-17",
  "Id": "example-ID",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Service": "s3.amazonaws.com"  
    },
    "Action": "SNS:Publish",
    "Resource": "${aws_sns_topic.hashing_bucket_notifications.arn}",
    "Condition": {
      "ArnLike": { "aws:SourceArn": "${aws_s3_bucket.hashing_bucket.arn}" }
    }
  }]
}
  END_OF_POLICY
}

resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.hashing_bucket.id

  topic {
    topic_arn = aws_sns_topic.hashing_bucket_notifications.arn
    events = ["s3:ObjectCreated:*"]
    filter_prefix = "images/"
  }
}

resource "aws_sns_topic_subscription" "new_photos_to_hash" {
  topic_arn = aws_sns_topic.hashing_bucket_notifications.arn
  protocol = "sqs"
  endpoint = module.pdq-hasher.input_queue_arn
}

resource "aws_sqs_queue_policy" "test" {
  queue_url = module.pdq-hasher.input_queue_id

  policy = <<END_OF_POLICY
{
  "Version": "2012-10-17",
  "Id": "sqspolicy",
  "Statement": [
    {
      "Sid": "First",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "sqs:SendMessage",
      "Resource": "${module.pdq-hasher.input_queue_arn}",
      "Condition": {
        "ArnEquals": {
          "aws:SourceArn": "${aws_sns_topic.hashing_bucket_notifications.arn}"
        }
      }
    }
  ]
}
END_OF_POLICY
}

module "pdq-hasher" {
  source = "./pdq-hasher"
  prefix = var.prefix
  lambda_docker_uri = var.hma_lambda_docker_uri
}

resource "aws_sns_topic_subscription" "new_hashes_to_match" {
  topic_arn = module.pdq-hasher.output_topic_arn
  protocol = "sqs"
  endpoint = module.pdq-matcher.input_queue_arn
}

module "pdq-matcher" {
  source = "./pdq-matcher"
  prefix = var.prefix
  lambda_docker_uri = var.hma_lambda_docker_uri
}

