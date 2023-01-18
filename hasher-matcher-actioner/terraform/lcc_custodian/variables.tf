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


variable "additional_tags" {
  description = "Additional resource tags"
  type        = map(string)
}

variable "custodian_frequency" {
  description = "How long to wait between squashing records. Must be an AWS Rate Expression. See here: https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html"
  type        = string
}
