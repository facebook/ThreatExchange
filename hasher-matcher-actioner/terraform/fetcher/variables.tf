# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

variable "prefix" {
  description = "Prefix to use for resource names"
  type        = string
}

variable "secrets_prefix" {
  description = "Prefix for all AWS Secrets created by the enduser."
  type        = string
}

variable "lambda_docker_info" {
  description = "Docker container information for lambda functions"
  type = object({
    uri = string
    commands = object({
      fetcher = string
    })
  })
}


variable "datastore" {
  description = "DynamoDB Table to store hash and match information into"
  type = object({
    name = string
    arn  = string
  })
}

variable "threat_exchange_data" {
  description = "Configuration information for the S3 Bucket that will hold ThreatExchange Data. data_folder is actually just a key prefix to search for but this is displyed as a folder in AWS UI"
  type = object({
    bucket_name = string
    data_folder = string
  })
}

variable "additional_tags" {
  description = "Additional resource tags"
  type        = map(string)
}

variable "log_retention_in_days" {
  description = "How long to retain cloudwatch logs for lambda functions in days"
  type        = number
}

variable "fetch_frequency" {
  description = "How long to wait between calls to ThreatExcahnge. Must be an AWS Rate Expression. See here: https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html"
  type        = string
}

variable "te_api_token_secret" {
  description = "The aws secret where the ThreatExchange API token is stored"
  type = object({
    name = string
    arn  = string
  })
}

variable "config_table" {
  description = "The name and arn of the DynamoDB table used for persisting configs."
  type = object({
    arn  = string
    name = string
  })
}
