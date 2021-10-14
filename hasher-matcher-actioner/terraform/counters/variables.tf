# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

variable "prefix" {
  description = "Prefix to use for resource names"
  type        = string
}

variable "lambda_docker_info" {
  description = "Docker container information for lambda functions"
  type = object({
    uri = string
    commands = object({
      ddb_stream_counter = string
    })
  })
}

variable "counts_datastore" {
  description = "The DynamoDBTable we'll be writing counts to."
  type = object({
    name = string
    arn  = string
  })
}

variable "log_retention_in_days" {
  description = "How long to retain cloudwatch logs for lambda functions in days"
  type        = number
}

variable "source_stream_arn" {
  description = "ARN for a DynamoDB Stream"
  type        = string
}

variable "source_table_name" {
  description = "Table for which this stream is configured."
  type        = string
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
