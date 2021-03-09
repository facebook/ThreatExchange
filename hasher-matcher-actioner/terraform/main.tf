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

locals {
  common_tags = {
    "HMAPrefix" = var.prefix
  }
}

module "hashing_data" {
  source          = "./hashing-data"
  prefix          = var.prefix
  additional_tags = local.common_tags
}

module "pdq_signals" {
  source = "./pdq-signals"
  prefix = var.prefix
  lambda_docker_info = {
    uri = var.hma_lambda_docker_uri
    commands = {
      matcher = "hmalib.lambdas.pdq.pdq_matcher.lambda_handler"
      hasher  = "hmalib.lambdas.pdq.pdq_hasher.lambda_handler"
      indexer = "hmalib.lambdas.pdq.pdq_indexer.lambda_handler"
    }
  }
  datastore = {
    name = module.hashing_data.hma_datastore.name
    arn  = module.hashing_data.hma_datastore.arn
  }
  images_input = {
    input_queue = aws_sqs_queue.pdq_images_queue.arn
    resource_list = [
      "arn:aws:s3:::${module.hashing_data.image_folder_info.bucket_name}/${module.hashing_data.image_folder_info.key}*"
    ]
  }
  threat_exchange_data = {
    bucket_name        = module.hashing_data.threat_exchange_data_folder_info.bucket_name
    pdq_data_file_key  = "${module.hashing_data.threat_exchange_data_folder_info.key}pdq.te"
    notification_topic = module.hashing_data.threat_exchange_data_folder_info.notification_topic
  }
  index_data_storage = {
    bucket_name      = module.hashing_data.index_folder_info.bucket_name
    index_folder_key = module.hashing_data.index_folder_info.key
  }
  matches_sns_topic_arn = aws_sns_topic.matches.arn

  log_retention_in_days = var.log_retention_in_days
  additional_tags       = local.common_tags
  measure_performance   = var.measure_performance
}

module "fetcher" {
  source = "./fetcher"
  prefix = var.prefix
  lambda_docker_info = {
    uri = var.hma_lambda_docker_uri
    commands = {
      fetcher = "hmalib.lambdas.fetcher.lambda_handler"
    }
  }
  threat_exchange_data = {
    bucket_name       = module.hashing_data.threat_exchange_data_folder_info.bucket_name
    pdq_data_file_key = "${module.hashing_data.threat_exchange_data_folder_info.key}pdq.te"
  }

  log_retention_in_days = var.log_retention_in_days
  additional_tags       = local.common_tags
}

resource "aws_sns_topic" "matches" {
  name_prefix = "${var.prefix}-matches"
}

# Connect Hashing Data to PDQ Signals

resource "aws_sqs_queue" "pdq_images_queue" {
  name_prefix                = "${var.prefix}-pdq-images"
  visibility_timeout_seconds = 300
  message_retention_seconds  = 1209600
  tags = merge(
    local.common_tags,
    {
      Name = "PDQImagesQueue"
    }
  )
}

resource "aws_sns_topic_subscription" "hash_new_images" {
  topic_arn = module.hashing_data.image_folder_info.notification_topic
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.pdq_images_queue.arn
}

data "aws_iam_policy_document" "pdq_hasher_queue" {
  statement {
    effect    = "Allow"
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.pdq_images_queue.arn]
    principals {
      type        = "Service"
      identifiers = ["sns.amazonaws.com"]
    }
    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = [module.hashing_data.image_folder_info.notification_topic]
    }
  }
}

resource "aws_sqs_queue_policy" "pdq_hasher_queue" {
  queue_url = aws_sqs_queue.pdq_images_queue.id
  policy    = data.aws_iam_policy_document.pdq_hasher_queue.json
}


# Connect Hashing Data to API

module "api" {
  source = "./api"
  prefix = var.prefix
  lambda_docker_info = {
    uri = var.hma_lambda_docker_uri
    commands = {
      status_api = "hmalib.lambdas.api.status_api.lambda_handler"
    }
  }
  datastore = {
    name = module.hashing_data.hma_datastore.name
    arn  = module.hashing_data.hma_datastore.arn
  }
 
  log_retention_in_days = var.log_retention_in_days
  additional_tags       = local.common_tags
}

