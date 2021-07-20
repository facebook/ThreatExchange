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

variable "local_image_buckets" {
  description = "Names and arns of s3 buckets to consider as inputs to HMA. All images uploaded to these buckets will be processed by the hasher"
  type        = list(object({
    name = string
    arn  = string
  }))
}

variable "lambda_docker_info" {
  description = "Docker container information for lambda functions"
  type = object({
    uri = string
    commands = object({
      local_bucket_hasher = string
    })
  })
}

variable "log_retention_in_days" {
  description = "How long to retain cloudwatch logs for lambda functions in days"
  type        = number
}

variable "datastore" {
  description = "DynamoDB Table to store a record of actions"
  type = object({
    name = string
    arn  = string
  })
}

variable "images_topic_arn" {
  description = "SNS Topic for publishing image submission requests"
  type        = string
}

variable "pdq_images_queue" {
  description = "SQS queue to send images to the pdq_hasher"
  type        = object({
    id = string
    arn  = string
  })
}

