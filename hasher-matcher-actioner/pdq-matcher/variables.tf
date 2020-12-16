# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

variable "region" {
  description = "AWS region to deploy to"
  type = string
  default = "us-east-1"
}

variable "profile" {
  description = "AWS profile to use for authentication"
  type = string
  default = null
}

variable "prefix" {
  description = "Prefix to use for resource names"
  type = string
}

variable "lambda_docker_uri" {
  description = "URI for docker container image to use for lambda function"
  type = string
}

variable "lambda_docker_command" {
  description = "command override for docker lambda container"
  type = string
  default = "pdq_matcher.lambda_handler"
}
