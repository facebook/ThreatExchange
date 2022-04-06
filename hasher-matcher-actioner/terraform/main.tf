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
  te_data_folder             = module.hashing_data.threat_exchange_data_folder_info.key
  te_api_token_secret_name   = "threatexchange/${var.prefix}_api_tokens"
  hma_api_tokens_secret_name = "hma/${var.prefix}_api_tokens"

  durable_storage_path = "/mnt/durable-storage"
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

  data_bucket = {
    bucket_name = aws_s3_bucket.data_bucket.id
    bucket_arn  = aws_s3_bucket.data_bucket.arn
  }
  submissions_queue = {
    queue_arn = aws_sqs_queue.submissions_queue.arn
    queue_url = aws_sqs_queue.submissions_queue.id
  }
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

  banks_datastore = module.datastore.banks_datastore

  log_retention_in_days = var.log_retention_in_days
  additional_tags       = merge(var.additional_tags, local.common_tags)
  measure_performance   = var.measure_performance
  indexer_frequency     = var.indexer_frequency
  config_table          = local.config_table

}

module "counters" {
  # DynamoDB does not necessarily [1] send the table name to the stream processor.
  # So instead of relying on it, we configure multiple lambdas using the same
  # underlying code. Since there is a lot to configure per lambda, we replicate
  # the module instead of individual resources inside the module.

  # 1: https://stackoverflow.com/questions/35278881/how-to-get-the-table-name-in-aws-dynamodb-trigger-function

  for_each = {
    HMADataStore = module.datastore.primary_datastore.stream_arn
    HMABanks     = module.datastore.banks_datastore.stream_arn
  }

  source          = "./counters"
  prefix          = var.prefix
  additional_tags = merge(var.additional_tags, local.common_tags)

  lambda_docker_info = {
    uri = var.hma_lambda_docker_uri
    commands = {
      ddb_stream_counter = "hmalib.lambdas.ddb_stream_counter.lambda_handler"
    }
  }

  source_stream_arn = each.value
  source_table_type = each.key

  counts_datastore = {
    name = module.datastore.counts_datastore.name
    arn  = module.datastore.counts_datastore.arn
  }

  log_retention_in_days = var.log_retention_in_days
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

  datastore = module.datastore.primary_datastore

  threat_exchange_data = {
    bucket_name = module.hashing_data.threat_exchange_data_folder_info.bucket_name
    data_folder = local.te_data_folder
  }

  log_retention_in_days = var.log_retention_in_days
  additional_tags       = merge(var.additional_tags, local.common_tags)
  fetch_frequency       = var.fetch_frequency

  te_api_token_secret = aws_secretsmanager_secret.te_api_token
  config_table        = local.config_table
}

resource "aws_sns_topic" "matches" {
  name_prefix = "${var.prefix}-matches"
}

# Set up webapp resources (s3 bucket and cloudfront distribution)

module "webapp" {
  source                          = "./webapp"
  prefix                          = var.prefix
  organization                    = var.organization
  include_cloudfront_distribution = var.include_cloudfront_distribution
}

/**
 * # Authentication:
 * authentication is currently handled in two ways:
 * 1) list of permanent access tokens stored in aws secrets
 * 2) user accesss via a dedicated or shared Cognito user pool   
 * 
 * Both methods are validated in an lambda: module.api.aws_lambda_function.api_auth
 * before being sent along to the rests of the system.
 */


resource "aws_secretsmanager_secret" "hma_api_tokens" {
  name                    = local.hma_api_tokens_secret_name
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "hma_api_tokens" {
  secret_id     = aws_secretsmanager_secret.hma_api_tokens.id
  secret_string = jsonencode(var.integration_api_access_tokens)
}


# Set up Cognito for authenticating webapp and api (unless shared setup is indicated in terraform.tfvars)

module "authentication" {
  source                                    = "./authentication"
  prefix                                    = var.prefix
  organization                              = var.organization
  use_cloudfront_distribution_url           = var.include_cloudfront_distribution && !var.use_shared_user_pool
  cloudfront_distribution_url               = "https://${module.webapp.cloudfront_distribution_domain_name}"
  use_shared_user_pool                      = var.use_shared_user_pool
  webapp_and_api_shared_user_pool_id        = var.webapp_and_api_shared_user_pool_id
  webapp_and_api_shared_user_pool_client_id = var.webapp_and_api_shared_user_pool_client_id
}

module "durable_fs" {
  source          = "./durable-fs"
  prefix          = var.prefix
  additional_tags = var.additional_tags
}

module "custodian" {
  source              = "./custodian"
  prefix              = var.prefix
  additional_tags     = merge(var.additional_tags, local.common_tags)
  custodian_frequency = var.custodian_frequency
  lambda_docker_info = {
    uri = var.hma_lambda_docker_uri
  }
}


/**
 * # Primary S3 Bucket:
 * Jack-of-all-trades S3 bucket. Used for storing raw data from threatexchange,
 * checkpoints, and upload-type media submissions.
 *
 * Inside another module (hashing-data), we create a couple of notification
 * configs on this bucket.
 */
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

/**
 * # Banks S3 Media Bucket:
 * Stores media uploaded by bank admins. Store raw data. Should ideally be
 * closed to the wider internet and can have retention rules based on legal
 * policy.
 */
resource "aws_s3_bucket" "banks_media_bucket" {
  bucket_prefix = "${var.prefix}-banks-media-"
  acl           = "private"
  tags = merge(
    var.additional_tags,
    {
      Name = "BanksMediaBucket"
    }
  )

  versioning {
    # Don't see a reason for versioning media. Everything will be keyed on uuid
    # and current date. 
    enabled = false
  }

  cors_rule {
    # The webapp uploads media to this bucket directly.
    allowed_headers = ["*"]
    allowed_methods = ["PUT"]

    # Partners could lock this down to specific origin where possible.
    allowed_origins = ["*"]
    max_age_seconds = 3000
  }

  lifecycle {
    # To prevent execution of plans which would cause this bucket to get
    # destroyed. Once in the hands of partners, we have to be extra careful to
    # not accidentally delete their data. 
    prevent_destroy = true
  }
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
resource "aws_sqs_queue" "submissions_queue_dlq" {
  name_prefix                = "${var.prefix}-submissions-deadletter-"
  visibility_timeout_seconds = 300
  message_retention_seconds  = var.deadletterqueue_message_retention_seconds

  tags = merge(
    var.additional_tags,
    local.common_tags,
    {
      Name = "SubmissionDLQ"
    }
  )
}

resource "aws_sqs_queue" "submissions_queue" {
  name_prefix                = "${var.prefix}-submissions"
  visibility_timeout_seconds = 300

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.submissions_queue_dlq.arn
    maxReceiveCount     = 4
  })

  tags = merge(
    var.additional_tags,
    local.common_tags,
    {
      Name = "SubmissionsQueue"
    }
  )
}

resource "aws_sqs_queue" "hashes_queue_dlq" {
  name_prefix                = "${var.prefix}-hashes-deadletter-"
  visibility_timeout_seconds = 300
  message_retention_seconds  = var.deadletterqueue_message_retention_seconds

  tags = merge(
    var.additional_tags,
    local.common_tags,
    {
      Name = "HashesDLQ"
    }
  )
}

resource "aws_sqs_queue" "hashes_queue" {
  name_prefix                = "${var.prefix}-hashes"
  visibility_timeout_seconds = 300

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.hashes_queue_dlq.arn
    maxReceiveCount     = 4
  })

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

  datastore       = module.datastore.primary_datastore
  banks_datastore = module.datastore.banks_datastore
  submissions_queue = {
    arn = aws_sqs_queue.submissions_queue.arn
  }

  hashes_queue = {
    arn = aws_sqs_queue.hashes_queue.arn
    url = aws_sqs_queue.hashes_queue.id
  }

  image_data_storage = {
    bucket_name  = module.hashing_data.image_folder_info.bucket_name
    image_prefix = module.hashing_data.image_folder_info.key
    all_bucket_arns = concat(
      [
        "arn:aws:s3:::${module.hashing_data.image_folder_info.bucket_name}/${module.hashing_data.image_folder_info.key}*"
      ],
      [for partner_bucket in var.partner_image_buckets : "${partner_bucket.arn}/*"]
    )
  }

  durable_fs_subnet_ids         = module.durable_fs.durable_fs_subnet_ids
  durable_fs_security_group_ids = module.durable_fs.durable_fs_security_group_ids
  durable_fs_arn                = module.durable_fs.durable_fs_arn
  durable_fs_local_mount_path   = local.durable_storage_path

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

  banks_datastore = module.datastore.banks_datastore

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
  source                      = "./api"
  prefix                      = var.prefix
  api_and_webapp_user_pool_id = module.authentication.webapp_and_api_user_pool_id
  api_authorizer_audience     = module.authentication.webapp_and_api_user_pool_client_id
  lambda_docker_info = {
    uri = var.hma_lambda_docker_uri
    commands = {
      api_root = "hmalib.lambdas.api.api_root.lambda_handler"
      api_auth = "hmalib.lambdas.api.api_auth.lambda_handler"
    }
  }
  datastore        = module.datastore.primary_datastore
  banks_datastore  = module.datastore.banks_datastore
  counts_datastore = module.datastore.counts_datastore

  image_data_storage = {
    bucket_name  = module.hashing_data.image_folder_info.bucket_name
    image_prefix = module.hashing_data.image_folder_info.key
  }

  index_data_storage = {
    bucket_name      = module.hashing_data.index_folder_info.bucket_name
    index_folder_key = module.hashing_data.index_folder_info.key
  }
  threat_exchange_data = {
    bucket_name = module.hashing_data.threat_exchange_data_folder_info.bucket_name
    data_folder = local.te_data_folder
  }

  banks_media_storage = {
    bucket_name = aws_s3_bucket.banks_media_bucket.id
    bucket_arn  = aws_s3_bucket.banks_media_bucket.arn
  }

  log_retention_in_days        = var.log_retention_in_days
  additional_tags              = merge(var.additional_tags, local.common_tags)
  config_table                 = local.config_table
  measure_performance          = var.measure_performance
  te_api_token_secret          = aws_secretsmanager_secret.te_api_token
  hma_api_access_tokens_secret = aws_secretsmanager_secret.hma_api_tokens

  writebacks_queue      = module.actions.writebacks_queue
  indexer_function_name = module.indexer.indexer_function_name
  indexer_function_arn  = module.indexer.indexer_function_arn
  hashes_queue = {
    url = aws_sqs_queue.hashes_queue.id,
    arn = aws_sqs_queue.hashes_queue.arn
  }
  submissions_queue = {
    url = aws_sqs_queue.submissions_queue.id,
    arn = aws_sqs_queue.submissions_queue.arn
  }
  partner_image_buckets              = var.partner_image_buckets
  enable_partner_upload_notification = var.enable_partner_upload_notification

  api_in_vpc      = var.api_in_vpc
  vpc_id          = var.vpc_id
  vpc_subnets     = var.vpc_subnets
  security_groups = var.security_groups
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
    command = "aws s3 sync ../webapp/build s3://${module.webapp.s3_bucket_name} --acl ${var.include_cloudfront_distribution ? "private" : "public-read"}"
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

  deadletterqueue_message_retention_seconds = var.deadletterqueue_message_retention_seconds
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


### New Submission Path (Use SNS topic instead of HTTP API) ###
module "submit_events" {
  count  = var.create_submit_event_sns_topic_and_handler ? 1 : 0
  source = "./submit_events"
  prefix = var.prefix
  lambda_docker_info = {
    uri = var.hma_lambda_docker_uri
    commands = {
      submit_event_handler = "hmalib.lambdas.submit_event_handler.lambda_handler"
    }
  }
  datastore = module.datastore.primary_datastore

  log_retention_in_days = var.log_retention_in_days
  additional_tags       = merge(var.additional_tags, local.common_tags)

  submissions_queue = {
    url = aws_sqs_queue.submissions_queue.id,
    arn = aws_sqs_queue.submissions_queue.arn
  }
  partner_image_buckets = var.partner_image_buckets

  deadletterqueue_message_retention_seconds = var.deadletterqueue_message_retention_seconds
}



### Basic Dashboard ###
locals {
  # Since module submit_event may or may not be initialized
  is_submit_event_module_initialized = length(module.submit_events) != 0
}

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
    (["Hash", module.hasher.hasher_function_name]),
    (["Match", module.matcher.matcher_function_name]),
    (["Action Evaluator", module.actions.action_evaluator_function_name]),
    (["Action Performer", module.actions.action_performer_function_name])
  ] # Not currently included fetcher, indexer, writebacker, and counter functions

  api_lambda_name  = module.api.api_root_function_name
  auth_lambda_name = module.api.api_auth_function_name
  other_lambdas = concat([
    module.fetcher.fetcher_function_name,
    module.indexer.indexer_function_name,
    module.actions.writebacker_function_name,
    module.api.api_auth_function_name,
    module.api.api_root_function_name,
    ], # all lambdas not given as pipeline_lambdas

    # optionally add submit module lambda if initialized.
    local.is_submit_event_module_initialized ? [module.submit_events[0].submit_event_handler_function_name] : []
  )

  queues_to_monitor = [
    (["ImageQueue", aws_sqs_queue.submissions_queue.name, aws_sqs_queue.submissions_queue_dlq.name]),
    (["HashQueue", aws_sqs_queue.hashes_queue.name, aws_sqs_queue.hashes_queue_dlq.name]),
    (["MatchQueue", module.actions.matches_queue_name, module.actions.matches_dlq_name]),
    (["ActionQueue", module.actions.actions_queue_name, module.actions.actions_dlq_name])
  ] # Could also monitor sns topics

  submit_event_lambda_name = local.is_submit_event_module_initialized ? module.submit_events[0].submit_event_handler_function_name : null
  submit_event_queue       = local.is_submit_event_module_initialized ? (["SubmitEventQueue", module.submit_events[0].submit_event_queue_name, module.submit_events[0].submit_event_dlq_name]) : null

  api_gateway_id = module.api.api_gateway_id
}
