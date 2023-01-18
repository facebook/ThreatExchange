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

variable "banks_datastore" {
  description = "DynamoDB Table to store bank information into"
  type = object({
    name = string
    arn  = string
  })
}

variable "submissions_queue" {
  description = "Configuration information for the image content that will be process for PDQ hashes"
  type = object({
    arn = string
  })
}

variable "hashes_queue" {
  description = "Output queue to push new hashes on"
  type = object({
    arn = string
    url = string
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

variable "image_data_storage" {
  description = "Where does the submission API upload images? all_bucket_arns must include image storage bucket and all partner buckets."

  type = object({
    bucket_name     = string
    image_prefix    = string
    all_bucket_arns = list(string)
  })
}

variable "durable_fs_security_group_ids" {
  description = "SG Ids for the durable file-system we are mounting on the hashing lambda."
  type        = list(string)
}

variable "durable_fs_subnet_ids" {
  description = "subnet Ids for the durable file-system we are mounting on the hashing lambda."
  type        = list(string)
}

variable "durable_fs_local_mount_path" {
  description = "Local mount path durable file-system we are mounting on the hashing lambda."
  type        = string
}

variable "durable_fs_arn" {
  description = "ARN for the durable file-system we are mounting on the hashing lambda."
  type        = string
}
