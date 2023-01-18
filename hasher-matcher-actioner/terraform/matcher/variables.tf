# Copyright (c) Meta Platforms, Inc. and affiliates.

variable "prefix" {
  description = "Prefix to use for resource names"
  type        = string
}

variable "lambda_docker_info" {
  description = "Docker container information for lambda functions"
  type = object({
    uri = string
  })
}

variable "datastore" {
  description = "DynamoDB Table to store hash and match information into"
  type = object({
    name = string
    arn  = string
  })
}

variable "hashes_queue" {
  description = "Queue from which to pull hashes to match"
  type = object({
    arn = string
    url = string
  })
}

variable "matches_topic_arn" {
  description = "SNS Topic to which we'll publish matches"
  type        = string
}

variable "index_data_storage" {
  description = "Configuration information for the S3 Bucket that will hold PDQ Index data"
  type = object({
    bucket_name      = string
    index_folder_key = string
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

variable "measure_performance" {
  description = "Send metrics to cloudwatch. Useful for benchmarking, but can incur costs. Set to string True for this to work."
  type        = bool
}

variable "metrics_namespace" {
  description = "Cloudwatch namespace for metrics."
  type        = string
  default     = "ThreatExchange/HMA"
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
