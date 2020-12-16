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
  source            = "./pdq-hasher"
  prefix            = var.prefix
  lambda_docker_uri = var.hma_lambda_docker_uri
  input_queue_arn   = aws_sqs_queue.pdq_hasher_new_file_queue.arn
  s3_images_arn     = "${module.hashing_data.data_bucket_arn}/${module.hashing_data.image_folder_key}"
}

module "pdq_matcher" {
  source            = "./pdq-matcher"
  prefix            = var.prefix
  lambda_docker_uri = var.hma_lambda_docker_uri
  input_queue_arn   = aws_sqs_queue.pdq_matcher_new_hash_queue.arn
}

resource "aws_sqs_queue" "pdq_hasher_new_file_queue" {
  name_prefix                = "${var.prefix}-pdq-hasher-input"
  visibility_timeout_seconds = 60
  message_retention_seconds  = 1209600
}

resource "aws_sqs_queue" "pdq_matcher_new_hash_queue" {
  name_prefix                = "${var.prefix}-pdq-matcher"
  visibility_timeout_seconds = 60
  message_retention_seconds  = 1209600
}

# Connect Hashing Data to PDQ Hasher

resource "aws_sns_topic_subscription" "hash_new_images" {
  topic_arn = module.hashing_data.image_notification_topic_arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.pdq_hasher_new_file_queue.arn
}

data "aws_iam_policy_document" "pdq_hasher_queue" {
  statement {
    effect    = "Allow"
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.pdq_hasher_new_file_queue.arn]
    principals {
      type        = "*"
      identifiers = ["*"]
    }
    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = [module.hashing_data.image_notification_topic_arn]
    }
  }
}

resource "aws_sqs_queue_policy" "pdq_hasher_queue" {
  queue_url = aws_sqs_queue.pdq_hasher_new_file_queue.id
  policy    = data.aws_iam_policy_document.pdq_hasher_queue.json
}

# Connect PDQ Hasher to PDQ Matcher

resource "aws_sns_topic_subscription" "match_new_hashes" {
  topic_arn = module.pdq_hasher.output_topic_arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.pdq_matcher_new_hash_queue.arn
}

data "aws_iam_policy_document" "pdq_matcher_queue" {
  statement {
    effect    = "Allow"
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.pdq_matcher_new_hash_queue.arn]
    principals {
      type        = "*"
      identifiers = ["*"]
    }
    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = [module.pdq_hasher.output_topic_arn]
    }
  }
}

resource "aws_sqs_queue_policy" "pdq_matcher_queue" {
  queue_url = aws_sqs_queue.pdq_matcher_new_hash_queue.id
  policy    = data.aws_iam_policy_document.pdq_matcher_queue.json
}
