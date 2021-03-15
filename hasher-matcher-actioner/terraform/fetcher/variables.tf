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
  description = "Configuration information for the S3 Bucket that will hold ThreatExchange Data"
  type = object({
    bucket_name       = string
    pdq_data_file_key = string
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

variable "fetch_frequency_min" {
  description = "How many minutes to wait between queries to ThreatExchange for updates"
  type        = number
  default     = 15
}

variable "te_api_token" {
  description = "Token to read data from ThreatExchange"
  type        = string
  sensitive   = true
}
