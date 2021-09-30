# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

variable "matches_sns_topic_arn" {
  description = "ARN for the topic that collects matches from matchers."
  type        = string
}

variable "lambda_docker_info" {
  description = "Docker container information for lambda functions"
  type = object({
    uri = string
    commands = object({
      action_evaluator = string
      action_performer = string
      writebacker      = string
    })
  })
}

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
  default     = {}
}

variable "measure_performance" {
  description = "Send metrics to cloudwatch. Useful for benchmarking, but can incur costs. Set to string True for this to work."
  type        = bool
  default     = false
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

variable "datastore" {
  description = "DynamoDB Table to store a record of actions"
  type = object({
    name = string
    arn  = string
  })
}

variable "queue_batch_size" {
  description = "Batch size for the matches queue to wait for before sending messages to lambda."
  type        = number
  default     = 100
}

variable "queue_window_in_seconds" {
  description = "Maximum batching window in seconds to wait before sending messages to lambda"
  type        = number
  default     = 30
}
