# Copyright (c) Meta Platforms, Inc. and affiliates.

variable "prefix" {
  description = "Prefix to use for resource names"
  type        = string
}

variable "secrets_prefix" {
  description = "Prefix for all AWS Secrets created by the enduser."
  type        = string
}

variable "api_and_webapp_user_pool_id" {
  description = "user pool id that can be used to create a URL to the JWT issuer (used by the api gateway authorizer)"
  type        = string
}

variable "api_authorizer_audience" {
  description = "The audience entry for the JWT authorizer (used by the api gateway authorizer; for Cognito integration, must be the app client id)"
  type        = string
}

variable "lambda_docker_info" {
  description = "Docker container information for lambda functions"
  type = object({
    uri = string
    commands = object({
      api_root = string
      api_auth = string
    })
  })
}

variable "image_data_storage" {
  description = "Configuration information for the S3 Bucket that will hold uploaded content"
  type = object({
    bucket_name  = string
    image_prefix = string
  })
}

variable "index_data_storage" {
  description = "Configuration information for the S3 Bucket that will hold PDQ Index data"
  type = object({
    bucket_name      = string
    index_folder_key = string
  })
}

variable "threat_exchange_data" {
  description = "Configuration information for the S3 Bucket that will hold ThreatExchange Data"
  type = object({
    bucket_name = string
    data_folder = string
  })
}

variable "datastore" {
  description = "DynamoDB Table to store hash and match information into"
  type = object({
    name = string
    arn  = string
  })
}


variable "banks_datastore" {
  description = "DynamoDB Table to store bank information into"
  type = object({
    name = string
    arn  = string
  })
}

variable "counts_datastore" {
  description = "The DynamoDBTable we be write counts to."
  type = object({
    name = string
    arn  = string
  })
}

variable "log_retention_in_days" {
  description = "How long to retain cloudwatch logs for lambda functions in days"
  type        = number
}

variable "additional_tags" {
  description = "Additional resource tags"
  type        = map(string)
}

variable "config_table" {
  description = "The name and arn of the DynamoDB table used for persisting configs."
  type = object({
    arn  = string
    name = string
  })
}

variable "te_api_token_secret" {
  description = "The aws secret where the ThreatExchange API token is stored"
  type = object({
    name = string
    arn  = string
  })
}

variable "hma_api_access_tokens_secret" {
  description = "The aws secret to the set of access tokens checked for in authorizer api as an alternative to cognito user tokens."
  type = object({
    name = string
    arn  = string
  })
}

variable "measure_performance" {
  description = "Send metrics to cloudwatch. Useful for benchmarking, but can incur costs. Set to string True for this to work."
  type        = bool
}

variable "writebacks_queue" {
  description = "ARN and url to send writebacks to"
  type = object({
    url = string
    arn = string
  })
}

variable "submissions_queue" {
  description = "URL and ARN for submissions queue. Messages from the submission APIs will be dropped on this queue"
  type = object({
    url = string
    arn = string
  })
}

variable "hashes_queue" {
  description = "URL and ARN for unified hashes queue. Messages from the submission APIs will be dropped on this queue"
  type = object({
    url = string
    arn = string
  })
}

variable "partner_image_buckets" {
  description = "Names and arns of s3 buckets to consider as inputs to HMA. All images uploaded to these buckets will be processed by the hasher"
  type = list(object({
    name   = string
    arn    = string
    params = map(string)
  }))
}

variable "enable_partner_upload_notification" {
  description = "Enable the upload notfication of partner buckets if given."
  type        = bool
  default     = false
}

variable "banks_media_storage" {
  description = "Name and arn where we store bank media."
  type = object({
    bucket_name = string
    bucket_arn  = string
  })
}

variable "api_in_vpc" {
  description = "Should the API gateway used with HMA be made private behind a VPC. (Either way API will also require authorization)"
  type        = bool
}

variable "vpc_id" {
  description = "vpc that locks down the API and UI to the specfic vpc_subnets and security_groups. Required if api_in_vpc = true"
  type        = string
  default     = ""
}

variable "vpc_subnets" {
  description = "Subnet ids of the vpc given in for vpc_id. Required if api_in_vpc = true"
  type        = list(string)
  default     = []
}

variable "security_groups" {
  description = "Security group ids to be used with the vpc given in for vpc_id. Required if api_in_vpc = true"
  type        = list(string)
  default     = []
}

variable "indexer_function_name" {
  description = "Name of the lambda function that does indexing."
  type        = string
}

variable "indexer_function_arn" {
  description = "ARN of the lambda function that does indexing."
  type        = string
}
