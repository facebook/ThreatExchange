
# Copyright (c) Meta Platforms, Inc. and affiliates.

variable "prefix" {
  description = "Prefix to use for resource names"
  type        = string
}

variable "log_retention_in_days" {
  description = "How long to retain cloudwatch logs for lambda functions in days"
  type        = number
}

variable "additional_tags" {
  description = "Additional resource tags"
  type        = map(string)
}

variable "measure_performance" {
  description = "Send metrics to cloudwatch. Useful for benchmarking, but can incur costs. Set to string True for this to work."
  type        = bool
}

variable "threat_exchange_data" {
  description = "Configuration information for the S3 Bucket that will hold ThreatExchange Data"
  type = object({
    bucket_name = string
    data_folder = string
  })
}

variable "index_data_storage" {
  description = "Configuration information for the S3 Bucket that will hold PDQ Index data"
  type = object({
    bucket_name      = string
    index_folder_key = string
  })
}

variable "lambda_docker_info" {
  description = "Docker container information for lambda functions"
  type = object({
    uri = string
    commands = object({
      indexer = string
    })
  })
}

variable "indexer_frequency" {
  description = "How frequently do we want indexing run? Must be an AWS Rate Expression. See here: https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html"
  type        = string
}


variable "config_table" {
  description = "The name and arn of the DynamoDB table used for persisting configs."
  type = object({
    arn  = string
    name = string
  })
}

variable "banks_datastore" {
  description = "DynamoDB Table to store bank information into"
  type = object({
    name = string
    arn  = string
  })
}
