# Copyright (c) Meta Platforms, Inc. and affiliates.

variable "config_table" {
  description = "The name and arn of the DynamoDB table used for persisting configs."
  type = object({
    arn  = string
    name = string
  })
}
