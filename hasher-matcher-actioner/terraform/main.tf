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

data "aws_region" "default" {}

locals {
  common_tags = {
    "HMAPrefix" = var.prefix
  }
  pdq_file_extension   = ".pdq.te"
  te_data_folder       = module.hashing_data.threat_exchange_data_folder_info.key
  te_api_token_secret_name = "threatexchange/${var.prefix}_api_tokens"
}

### Config storage ###

resource "aws_dynamodb_table" "hma_config" {
  name         = "${var.prefix}-HMAConfig"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "ConfigType"
  range_key    = "ConfigName"

  attribute {
    name = "ConfigType"
    type = "S"
  }
  attribute {
    name = "ConfigName"
    type = "S"
  }

  tags = merge(
    var.additional_tags,
    {
      Name = "HMAConfig"
    }
  )
}

module "hashing_data" {
  source          = "./hashing-data"
  prefix          = var.prefix
  additional_tags = merge(var.additional_tags, local.common_tags)
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
    pdq_file_extension = local.pdq_file_extension
    data_folder        = local.te_data_folder
    notification_topic = module.hashing_data.threat_exchange_data_folder_info.notification_topic
  }
  index_data_storage = {
    bucket_name      = module.hashing_data.index_folder_info.bucket_name
    index_folder_key = module.hashing_data.index_folder_info.key
  }
  matches_sns_topic_arn = aws_sns_topic.matches.arn

  log_retention_in_days = var.log_retention_in_days
  additional_tags       = merge(var.additional_tags, local.common_tags)
  measure_performance   = var.measure_performance
}

module "fetcher" {
  source       = "./fetcher"
  prefix       = var.prefix
  te_api_token = var.te_api_token

  lambda_docker_info = {
    uri = var.hma_lambda_docker_uri
    commands = {
      fetcher = "hmalib.lambdas.fetcher.lambda_handler"
    }
  }

  datastore = {
    name = module.hashing_data.hma_datastore.name
    arn  = module.hashing_data.hma_datastore.arn
  }

  threat_exchange_data = {
    bucket_name = module.hashing_data.threat_exchange_data_folder_info.bucket_name
    data_folder = local.te_data_folder
  }
  collab_file = var.collab_file

  log_retention_in_days = var.log_retention_in_days
  additional_tags       = merge(var.additional_tags, local.common_tags)
  fetch_frequency       = var.fetch_frequency

  config_arn = aws_dynamodb_table.hma_config.arn
  te_api_token_secret  = aws_secretsmanager_secret.te_api_token
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
    var.additional_tags,
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

# Set up webapp resources (s3 bucket and cloudfront distribution)

module "webapp" {
  source                          = "./webapp"
  prefix                          = var.prefix
  organization                    = var.organization
  include_cloudfront_distribution = var.include_cloudfront_distribution && !var.use_shared_user_pool
}

# Set up Cognito for authenticating webapp and api (unless shared setup is indicated in terraform.tfvars)

module "authentication" {
  source                                    = "./authentication"
  prefix                                    = var.prefix
  organization                              = var.organization
  use_cloudfront_distribution_url           = var.include_cloudfront_distribution
  cloudfront_distribution_url               = "https://${module.webapp.cloudfront_distribution_domain_name}"
  use_shared_user_pool                      = var.use_shared_user_pool
  webapp_and_api_shared_user_pool_id        = var.webapp_and_api_shared_user_pool_id
  webapp_and_api_shared_user_pool_client_id = var.webapp_and_api_shared_user_pool_client_id
}

# Set up api

module "api" {
  source                    = "./api"
  prefix                    = var.prefix
  api_authorizer_jwt_issuer = "https://cognito-idp.${data.aws_region.default.name}.amazonaws.com/${module.authentication.webapp_and_api_user_pool_id}"
  api_authorizer_audience   = module.authentication.webapp_and_api_user_pool_client_id
  lambda_docker_info = {
    uri = var.hma_lambda_docker_uri
    commands = {
      api_root = "hmalib.lambdas.api.api_root.lambda_handler"
      api_auth = "hmalib.lambdas.api.api_auth.lambda_handler"
    }
  }
  datastore = {
    name = module.hashing_data.hma_datastore.name
    arn  = module.hashing_data.hma_datastore.arn
  }
  image_data_storage = {
    bucket_name      = module.hashing_data.image_folder_info.bucket_name
    image_folder_key = module.hashing_data.image_folder_info.key
  }
  threat_exchange_data = {
    bucket_name        = module.hashing_data.threat_exchange_data_folder_info.bucket_name
    pdq_file_extension = local.pdq_file_extension
    data_folder        = local.te_data_folder
  }

  log_retention_in_days = var.log_retention_in_days
  additional_tags       = merge(var.additional_tags, local.common_tags)
}

# Build and deploy webapp

resource "local_file" "webapp_env" {
  depends_on = [
    module.api.invoke_url,
    module.authentication.webapp_and_api_user_pool_id,
    module.authentication.webapp_and_api_user_pool_client_id
  ]
  sensitive_content = "REACT_APP_REGION=${data.aws_region.default.name}\nREACT_APP_USER_POOL_ID=${module.authentication.webapp_and_api_user_pool_id}\nREACT_APP_USER_POOL_APP_CLIENT_ID=${module.authentication.webapp_and_api_user_pool_client_id}\nREACT_APP_HMA_API_ENDPOINT=${module.api.invoke_url}\n"
  filename          = "../webapp/.env"
}

resource "null_resource" "build_and_deploy_webapp" {
  depends_on = [
    module.webapp.s3_bucket_name,
    local_file.webapp_env
  ]
  provisioner "local-exec" {
    command     = "npm install --silent"
    working_dir = "../webapp"
  }
  provisioner "local-exec" {
    command     = "npm run build"
    working_dir = "../webapp"
  }
  provisioner "local-exec" {
    command = "aws s3 sync ../webapp/build s3://${module.webapp.s3_bucket_name} --acl public-read"
  }
}

module "actions" {
  source = "./actions"

  prefix = var.prefix
  lambda_docker_info = {
    uri = var.hma_lambda_docker_uri
    commands = {
      action_evaluator = "hmalib.lambdas.actions.action_evaluator.lambda_handler"
      action_performer = "hmalib.lambdas.actions.action_performer.lambda_handler"
      reactioner       = "hmalib.lambdas.actions.reactioner.lambda_handler"
    }
  }

  matches_sns_topic_arn = aws_sns_topic.matches.arn

  log_retention_in_days = var.log_retention_in_days
  additional_tags       = merge(var.additional_tags, local.common_tags)
  measure_performance   = var.measure_performance
  te_api_token_secret      = aws_secretsmanager_secret.te_api_token
}

### ThreatExchange API Token Secret ###

resource "aws_secretsmanager_secret" "te_api_token" {
  name                    = local.te_api_token_secret_name
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "te_api_token" {
  secret_id     = aws_secretsmanager_secret.te_api_token.id
  secret_string = var.te_api_token
}
