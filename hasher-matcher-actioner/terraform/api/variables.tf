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

variable "api_access_token" {
  description = "access token checked for in authorizer api lambda"
  type        = string
  sensitive = true
}

variable "lambda_docker_info" {
  description = "Docker container information for lambda functions"
  type = object({
    uri = string
    commands = object({
      api_root = string
      api_auth = string
    })
  })
}

variable "image_data_storage" {
  description = "Configuration information for the S3 Bucket that will hold uploaded content"
  type = object({
    bucket_name     = string
    image_folder_key  = string
  })
}

variable "datastore" {
  description = "DynamoDB Table to store hash and match information into"
  type = object({
    name = string
    arn  = string
  })
}

variable "log_retention_in_days" {
  description = "How long to retain cloudwatch logs for lambda functions in days"
  type        = number
}

variable "additional_tags" {
  description = "Additional resource tags"
  type        = map(string)
  default     = {}
}


