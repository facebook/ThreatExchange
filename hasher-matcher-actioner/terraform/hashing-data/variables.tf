# Copyright (c) Meta Platforms, Inc. and affiliates.

variable "prefix" {
  description = "Prefix to use for resource names"
  type        = string
}

variable "additional_tags" {
  description = "Additional resource tags"
  type        = map(string)
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
