# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

variable "hma_lambda_docker_uri" {
  type        = string
  description = "The URI for the docker image to use for the hma lambdas"
}

variable "prefix" {
  description = "Prefix to use for resource names"
  type        = string
  default     = "hma"
}

variable "api_access_token" {
  description = "access token checked for in authorizer api lambda"
  type        = string
  sensitive = true
  default = "asupersecrettoken"  # Will replace before real data stored
}

variable "log_retention_in_days" {
  description = "How long to retain cloudwatch logs for lambda functions in days"
  type        = number
  default     = 14
}

variable "measure_performance" {
  description = "Send metrics to cloudwatch. Useful for benchmarking, but can incur costs. Set to string True for this to work."
  type        = bool
  default     = false
}

variable "metrics_namespace" {
  description = "Cloudwatch namespace for metrics."
  type        = string
  default     = "ThreatExchange/HMA"
}

variable "additional_tags" {
  description = "Additional resource tags. Will be applied to ALL resources created."
  type        = map(string)
  default     = {}
}

variable "include_cloudfront_distribution" {
  description = "Indicates whether a CloudFront distribution is included"
  type        = bool
  default     = false
}

variable "te_api_token" {
  description = "The secret token used to authenticate your access to ThreatExchange. You can find this by navigating to https://developers.facebook.com/tools/accesstoken/"
  type        = string
  sensitive   = true
}
