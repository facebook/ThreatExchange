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

variable "organization" {
  description = "The name / acronym to use for resource names that must be globally unique (use only lower case alpha a-z, and, optionally, hyphens)"
  type        = string
}

variable "log_retention_in_days" {
  description = "How long to retain cloudwatch logs for lambda functions in days"
  type        = number
  default     = 14
}

variable "measure_performance" {
  description = "Send metrics to cloudwatch and build a dashboard. Useful for benchmarking, but can incur costs. Set to string True for this to work."
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
  description = "The secret token used to authenticate your access to ThreatExchange. You can find this by navigating to https://developers.facebook.com/tools/accesstoken/. Leave blank if you would not like to fetch from ThreatExchange"
  type        = string
  sensitive   = true
}

variable "fetch_frequency" {
  description = "How long to wait between calls to ThreatExcahnge. Must be an AWS Rate Expression. See here: https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html"
  type        = string
  default     = "15 minutes"
}

variable "collab_file" {
  description = "An optional file name of ThreatExchange Collaborations objects to prepopulate. See collabs_example.json for the correct formatting"
  type        = string
  default     = "collabs_example.json"
}

variable "use_shared_user_pool" {
  description = "Indicates if the web app and api will use a shared user pool (generally true for developers / engineers sandbox environments, otherwise false)"
  type        = bool
  default     = false
}

variable "webapp_and_api_shared_user_pool_id" {
  description = "The id of the shared user pool. Used in conjunction with use_shared_user_pool set to true. Generate by running terraform init & apply from /authentication-shared."
  type        = string
  default     = ""
}

variable "webapp_and_api_shared_user_pool_client_id" {
  description = "The id of the shared user pool app client. Used in conjunction with use_shared_user_pool set to true. Generate by running terraform init & apply from /authentication-shared."
  type        = string
  default     = ""
}

variable "set_sqs_windows_to_min" {
  description = "The system's SQS Queues have a batch_size and timeout window configured for a production use case. If this var is set to true those values will be overridden and set to the minimum (helpful for fast one off testing)."
  type        = bool
  default     = false
}

variable "local_image_buckets" {
  description = "Names and arns of s3 buckets to consider as inputs to HMA. All images uploaded to these buckets will be processed by the hasher"
  type        = list(object({
    name = string
    arn  = string
  }))
  default     = []
}
