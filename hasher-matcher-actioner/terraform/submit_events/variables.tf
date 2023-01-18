# Copyright (c) Meta Platforms, Inc. and affiliates.

variable "prefix" {
  description = "Prefix to use for resource names"
  type        = string
}

variable "lambda_docker_info" {
  description = "Docker container information for lambda functions"
  type = object({
    uri = string
    commands = object({
      submit_event_handler = string
    })
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

variable "datastore" {
  description = "DynamoDB Table to store hash and match information into"
  type = object({
    name = string
    arn  = string
  })
}

variable "submissions_queue" {
  description = "URL and ARN for submissions queue. Messages from the submission APIs will be dropped on this queue"
  type = object({
    url = string
    arn = string
  })
}

variable "partner_image_buckets" {
  description = "Names and arns of s3 buckets to consider as inputs to HMA. All images uploaded to these buckets will be processed by the hasher"
  type = list(object({
    name   = string
    arn    = string
    params = map(string)
  }))
}

variable "deadletterqueue_message_retention_seconds" {
  description = "Number of second messages should stay in dead letter queue after a repeated failure."
  type        = number
}
