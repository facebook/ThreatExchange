# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

variable "region" {
  description = "AWS region to deploy to"
  type        = string
  default     = "us-east-1"
}

variable "prefix" {
  description = "Prefix to use for resource names"
  type        = string
}

variable "datastore" {
  description = "DynamoDB Table to store hash and match information into"
  type = object({
    name = string
    arn  = string
  })
}

variable "lambdas_to_monitor" {
  type    = list(string)
  default = null
}

variable "queues_to_monitor" {
  type    = list(string)
  default = null
}

variable "api_gateway_id" {
  type    = string
  default = null
}


