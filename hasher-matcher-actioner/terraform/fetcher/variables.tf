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

variable "lambda_docker_info" {
  description = "Docker container information for lambda functions"
  type = object({
    uri = string
    commands = object({
      fetcher = string
    })
  })
}

variable "threat_exchange_data" {
  description = "Configuration information for the S3 Bucket that will hold ThreatExchange Data. data_folder is actually just a key prefix to search for but this is displyed as a folder in AWS UI"
  type = object({
    bucket_name       = string
    data_folder       = string
  })
}

variable "additional_tags" {
  description = "Additional resource tags"
  type        = map(string)
  default     = {}
}

variable "log_retention_in_days" {
  description = "How long to retain cloudwatch logs for lambda functions in days"
  type        = number
}

variable "fetch_frequency" {
  description = "How long to wait between calls to ThreatExcahnge. Must be an AWS Rate Expression. See here: https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html"
  type        = string
}

variable "te_api_token" {
  description = "Token to read data from ThreatExchange"
  type        = string
  sensitive   = true
}

variable "collab_file" {
  description = "An optional file name of ThreatExchange Collaborations objects to prepopulate. See collabs_example.json for the correct formatting"
  type = string
}

variable "config_arn" {
  description = "The ARN of the DynamoDB table with configs"
  type = string
}