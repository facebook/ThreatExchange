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
      matcher = string
      hasher  = string
    })
  })
}

variable "images_input_queue_arn" {
  description = "ARN for SQS queue that will send new images events"
  type = string
}

variable "image_resource_list" {
  description = "List of resource ARNs where hasher should be able to pull images from"
  type        = list(string)
}

variable "s3_data_bucket_id" {
  description = "Name of bucket that holds the hash index files to match hashes"
  type        = string
}

variable "matches_sns_topic_arn" {
  description = "Output SNS topic to publish new matches to"
  type        = string
}

variable "s3_index_arn" {
  description = "ARN for folder in s3 that holds the hash index files to match hashes"
  type        = string
}
