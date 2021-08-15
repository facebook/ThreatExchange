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
  pdq_file_extension       = ".pdq.te"
  te_data_folder           = module.hashing_data.threat_exchange_data_folder_info.key
  te_api_token_secret_name = "threatexchange/${var.prefix}_api_tokens"
}

### Config storage ###

resource "aws_dynamodb_table" "config_table" {
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

  # TODO(dcallies) allow creation of initial configs
  # provisioner "local-exec" {
  #  command = "python3 ../scripts/populate_config_db ${var.collab_file} ${aws_dynamodb_table.threatexchange_config.name}"
  # }
}

locals {
  config_table = {
    arn  = aws_dynamodb_table.config_table.arn
    name = aws_dynamodb_table.config_table.name
  }
}

module "datastore" {
  source          = "./datastore"
  prefix          = var.prefix
  additional_tags = merge(var.additional_tags, local.common_tags)
}

module "hashing_data" {
  source          = "./hashing-data"
  prefix          = var.prefix
  additional_tags = merge(var.additional_tags, local.common_tags)
}

module "indexer" {
  source = "./indexer"
  prefix = var.prefix
  lambda_docker_info = {
    uri = var.hma_lambda_docker_uri

    commands = {
      indexer = "hmalib.lambdas.unified_indexer.lambda_handler"
    }
  }
  threat_exchange_data = {
    bucket_name        = module.hashing_data.threat_exchange_data_folder_info.bucket_name
    data_folder        = local.te_data_folder
    notification_topic = module.hashing_data.threat_exchange_data_folder_info.notification_topic
  }
  index_data_storage = {
    bucket_name      = module.hashing_data.index_folder_info.bucket_name
    index_folder_key = module.hashing_data.index_folder_info.key
  }

  log_retention_in_days = var.log_retention_in_days
  additional_tags       = merge(var.additional_tags, local.common_tags)
  measure_performance   = var.measure_performance
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
  datastore = module.datastore.primary_datastore

  images_input = {
    input_queue = aws_sqs_queue.pdq_images_queue.arn
    resource_list = concat(
      [
        "arn:aws:s3:::${module.hashing_data.image_folder_info.bucket_name}/${module.hashing_data.image_folder_info.key}*"
      ],
      [for partner_bucket in var.partner_image_buckets: "${partner_bucket.arn}/*"]
    )
    image_folder_key = module.hashing_data.image_folder_info.key
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
  config_table          = local.config_table

  queue_batch_size        = var.set_sqs_windows_to_min ? 10 : 100
  queue_window_in_seconds = var.set_sqs_windows_to_min ? 0 : 30
}

module "counters" {
  source          = "./counters"
  prefix          = var.prefix
  additional_tags = merge(var.additional_tags, local.common_tags)
  datastore       = module.datastore.primary_datastore
  lambda_docker_info = {
    uri = var.hma_lambda_docker_uri
    commands = {
      match_counter = "hmalib.lambdas.match_counter.lambda_handler"
    }
  }
  log_retention_in_days = var.log_retention_in_days
  measure_performance   = var.measure_performance
  matches_sns_topic_arn = aws_sns_topic.matches.arn
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

  datastore = module.datastore.primary_datastore

  threat_exchange_data = {
    bucket_name = module.hashing_data.threat_exchange_data_folder_info.bucket_name
    data_folder = local.te_data_folder
  }
  collab_file = var.collab_file

  log_retention_in_days = var.log_retention_in_days
  additional_tags       = merge(var.additional_tags, local.common_tags)
  fetch_frequency       = var.fetch_frequency

  te_api_token_secret = aws_secretsmanager_secret.te_api_token
  config_table        = local.config_table
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

/*
 * # Submissions SQS:
 * Submissions from the API are routed directly into a queue. Doing an SNS
 * indirection **could** allow multiple lambdas to be listening for submissions,
 * but, that would be costly because the lambda invocation would cost money.
 *
 * Instead, we will have a single hashing lambda capable of handling all
 * content_types. If the content, because of its size or because of compute
 * complexity can't be handled by this "base" lambda, it will be routed to
 * another specially capable lambda queue.
 *
 * - This should soon absorb the pdq_images queue + SNS topic as the only queue
 *   that we will publish submissions on.
 *   If we have proven that the generic lambda can generate PDQ signals, we can 
 *   do away with the PDQ specific infrastructure altogether.
*/
resource "aws_sqs_queue" "submissions_queue" {
  name_prefix                = "${var.prefix}-submissions"
  visibility_timeout_seconds = 300
  message_retention_seconds  = 1209600
  tags = merge(
    var.additional_tags,
    local.common_tags,
    {
      Name = "SubmissionsQueue"
    }
  )
}

resource "aws_sqs_queue" "hashes_queue" {
  name_prefix                = "${var.prefix}-hashes"
  visibility_timeout_seconds = 300
  message_retention_seconds  = 1209600
  tags = merge(
    var.additional_tags,
    local.common_tags,
    {
      Name = "HashesQueue"
    }
  )
}

module "hasher" {
  source = "./hasher"
  prefix = var.prefix
  lambda_docker_info = {
    uri = var.hma_lambda_docker_uri
  }

  datastore = module.datastore.primary_datastore
  submissions_queue = {
    arn = aws_sqs_queue.submissions_queue.arn
  }

  hashes_queue = {
    arn = aws_sqs_queue.hashes_queue.arn
    url = aws_sqs_queue.hashes_queue.id
  }

  log_retention_in_days = var.log_retention_in_days
  additional_tags       = merge(var.additional_tags, local.common_tags)
  config_table          = local.config_table
  measure_performance   = var.measure_performance
}

module "matcher" {
  source = "./matcher"
  prefix = var.prefix

  lambda_docker_info = {
    uri = var.hma_lambda_docker_uri
  }

  datastore = module.datastore.primary_datastore

  hashes_queue = {
    arn = aws_sqs_queue.hashes_queue.arn
    url = aws_sqs_queue.hashes_queue.id
  }

  matches_topic_arn = aws_sns_topic.matches.arn

  index_data_storage = {
    bucket_name      = module.hashing_data.index_folder_info.bucket_name
    index_folder_key = module.hashing_data.index_folder_info.key
  }

  log_retention_in_days = var.log_retention_in_days
  additional_tags       = merge(var.additional_tags, local.common_tags)
  config_table          = local.config_table
  measure_performance   = var.measure_performance
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
  datastore = module.datastore.primary_datastore
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
  config_table          = local.config_table
  measure_performance   = var.measure_performance
  te_api_token_secret   = aws_secretsmanager_secret.te_api_token

  writebacks_queue = module.actions.writebacks_queue
  images_topic_arn = module.hashing_data.image_folder_info.notification_topic

  submissions_queue = {
    url = aws_sqs_queue.submissions_queue.id,
    arn = aws_sqs_queue.submissions_queue.arn
  }
  partner_image_buckets = var.partner_image_buckets
}

# Build and deploy webapp

locals {
  dashboard_name    = "${var.prefix}-dashboard"
  aws_dashboard_url = var.measure_performance ? "https://console.aws.amazon.com/cloudwatch/home?region=${data.aws_region.default.name}#dashboards:name=${local.dashboard_name}" : ""
}

resource "local_file" "webapp_env" {
  depends_on = [
    module.api.invoke_url,
    module.authentication.webapp_and_api_user_pool_id,
    module.authentication.webapp_and_api_user_pool_client_id
  ]
  sensitive_content = "REACT_APP_AWS_DASHBOARD_URL=${local.aws_dashboard_url}\nREACT_APP_REGION=${data.aws_region.default.name}\nREACT_APP_USER_POOL_ID=${module.authentication.webapp_and_api_user_pool_id}\nREACT_APP_USER_POOL_APP_CLIENT_ID=${module.authentication.webapp_and_api_user_pool_client_id}\nREACT_APP_HMA_API_ENDPOINT=${module.api.invoke_url}\n"
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
      writebacker      = "hmalib.lambdas.actions.writebacker.lambda_handler"
    }
  }

  matches_sns_topic_arn = aws_sns_topic.matches.arn

  log_retention_in_days = var.log_retention_in_days
  additional_tags       = merge(var.additional_tags, local.common_tags)
  measure_performance   = var.measure_performance
  te_api_token_secret   = aws_secretsmanager_secret.te_api_token
  config_table = {
    name = aws_dynamodb_table.config_table.name
    arn  = aws_dynamodb_table.config_table.arn
  }
  datastore = module.datastore.primary_datastore

  queue_batch_size        = var.set_sqs_windows_to_min ? 10 : 100
  queue_window_in_seconds = var.set_sqs_windows_to_min ? 0 : 30
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


### Basic Dashboard ###
module "dashboard" {
  count = var.measure_performance ? 1 : 0
  depends_on = [
    module.api.api_root_function_name,
    module.datastore.primary_datastore,
  ]
  name      = local.dashboard_name
  source    = "./dashboard"
  prefix    = var.prefix
  datastore = module.datastore.primary_datastore
  pipeline_lambdas = [
    (["Hash", module.pdq_signals.pdq_hasher_function_name]),
    (["Match", module.pdq_signals.pdq_matcher_function_name]),
    (["Action Evaluator", module.actions.action_evaluator_function_name]),
    (["Action Performer", module.actions.action_performer_function_name])
  ] # Not currently included fetcher, indexer, writebacker, and counter functions
  api_lambda_name = module.api.api_root_function_name
  other_lambdas = [
    module.fetcher.fetcher_function_name,
    module.indexer.indexer_function_name,
    module.actions.writebacker_function_name,
    module.counters.match_counter_function_name
  ]
  queues_to_monitor = [
    (["ImageQueue", aws_sqs_queue.pdq_images_queue.name]),
    (["HashQueue", module.pdq_signals.hashes_queue_name]),
    (["MatchQueue", module.actions.matches_queue_name]),
    (["ActionQueue", module.actions.actions_queue_name])
  ] # Could also monitor sns topics
  api_gateway_id = module.api.api_gateway_id
}
