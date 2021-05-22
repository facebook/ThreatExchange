# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

variable "region" {
  description = "AWS region to deploy to"
  type        = string
  default     = "us-east-1"
}

variable "profile" {
  description = "AWS profile to use for authentication"
  type        = string
  default     = null
}

variable "prefix" {
  description = "Prefix to use for resource names"
  type        = string
}

variable "lambda_docker_info" {
  description = "Docker container information for lambda functions"
  type = object({
    uri = string
    commands = object({
      match_counter = string
    })
  })
}

variable "matches_sns_topic_arn" {
  description = "ARN for the topic that collects matches from matchers."
  type        = string
}

variable "log_retention_in_days" {
  description = "How long to retain cloudwatch logs for lambda functions in days"
  type        = number
}

variable "datastore" {
  description = "DynamoDB Table to store hash and match information into"
  type = object({
    name = string
    arn  = string
  })
}

variable "additional_tags" {
  description = "Additional resource tags"
  type        = map(string)
  default     = {}
}

variable "measure_performance" {
  description = "Send metrics to cloudwatch. Useful for benchmarking, but can incur costs. Set to string True for this to work."
  type        = bool
  default     = false
}
