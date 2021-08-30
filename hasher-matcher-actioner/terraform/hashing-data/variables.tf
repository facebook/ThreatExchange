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

variable "additional_tags" {
  description = "Additional resource tags"
  type        = map(string)
  default     = {}
}

variable "data_bucket" {
  description = "S3 bucket details. This S3 bucket will be used to store indexes, data, submissions"
  type = object({
    bucket_name = string
    bucket_arn  = string
  })
}

variable "submissions_queue" {
  description = "ARN of the queue to which we will route uploads."
  type = object({
    queue_arn = string
    queue_url = string
  })
}
