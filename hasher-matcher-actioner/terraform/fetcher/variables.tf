# Copyright (c) Meta Platforms, Inc. and affiliates.

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
