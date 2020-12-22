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

module "hashing_data" {
  source = "./hashing-data"
  prefix = var.prefix
}

module "pdq_hasher" {
  source = "./pdq-hasher"
}

module "pdq_matcher" {
  source = "./pdq-matcher"
}

module "pdq_signals" {
  source  = "./pdq-signals"
  region  = "us-east-1"
  profile = null
  prefix  = var.prefix
  lambda_docker_info = {
    uri = var.hma_lambda_docker_uri
    commands = {
      matcher = "pdq_matcher.lambda_handler"
      hasher  = "pdq_hasher.lambda_handler"
    }
  }
  images_input_queue_arn = aws_sqs_queue.pdq_images_queue.arn
  image_resource_list = [
    "${module.hashing_data.data_bucket_arn}/${module.hashing_data.image_folder_key}*"
  ]
  s3_data_bucket_id = module.hashing_data.data_bucket_id
  matches_sns_topic_arn = aws_sns_topic.matches.arn
  s3_index_arn      = "${module.hashing_data.data_bucket_arn}/${module.hashing_data.index_folder_key}"
}

resource "aws_sns_topic" "matches" {
  name_prefix = "${var.prefix}-matches"
}

# Connect Hashing Data to PDQ Signals

resource "aws_sns_topic_subscription" "hash_new_images" {
  topic_arn = module.hashing_data.image_notification_topic_arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.pdq_images_queue.arn
}

resource "aws_sqs_queue" "pdq_images_queue" {
  name_prefix                = "${var.prefix}-pdq-images"
  visibility_timeout_seconds = 300
  message_retention_seconds  = 1209600
}

data "aws_iam_policy_document" "pdq_hasher_queue" {
  statement {
    effect    = "Allow"
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.pdq_images_queue.arn]
    principals {
      type = "Service"
      identifiers = ["sns.amazonaws.com"]
    }
    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = [module.hashing_data.image_notification_topic_arn]
    }
  }
}

resource "aws_sqs_queue_policy" "pdq_hasher_queue" {
  queue_url = aws_sqs_queue.pdq_images_queue.id
  policy    = data.aws_iam_policy_document.pdq_hasher_queue.json
}
