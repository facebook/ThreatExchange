# Copyright (c) Meta Platforms, Inc. and affiliates.

variable "prefix" {
  description = "Prefix to use for resource names"
  type        = string
  default     = "hma"
}

variable "additional_tags" {
  description = "Additional resource tags. Will be applied to ALL resources created."
  type        = map(string)
  default     = {}
}

variable "submit_topic_arn" {
  description = "SNS Topic to which we'll publish submission events"
  type        = string
}
