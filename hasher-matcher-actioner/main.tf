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
}

module "pdq_matcher" {
  source            = "./pdq-matcher"
  prefix            = var.prefix
  lambda_docker_uri = var.hma_lambda_docker_uri
}

# Connect Hashing Data to PDQ Hasher

resource "aws_sns_topic_subscription" "hash_new_images" {
  topic_arn = module.hashing_data.image_notification_topic_arn
  protocol  = "sqs"
  endpoint  = module.pdq_hasher.input_queue_arn
}

data "aws_iam_policy_document" "pdq_hasher_queue" {
  statement {
    effect    = "Allow"
    actions   = ["sqs:SendMessage"]
    resources = [module.pdq_hasher.input_queue_arn]
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
  queue_url = module.pdq_hasher.input_queue_id
  policy    = data.aws_iam_policy_document.pdq_hasher_queue.json
}
