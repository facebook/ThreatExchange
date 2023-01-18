# Copyright (c) Meta Platforms, Inc. and affiliates.

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
  default     = ""
}

variable "fetch_frequency" {
  description = "How long to wait between calls to ThreatExcahnge. Must be an AWS Rate Expression. See here: https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html"
  type        = string
  default     = "15 minutes"
}

variable "indexer_frequency" {
  description = "How frequently do we want indexing run? Must be an AWS Rate Expression. See here: https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html"
  type        = string
  default     = "15 minutes"
}

variable "lcc_custodian_frequency" {
  description = "How frequently do we want indexing run? Must be an AWS Rate Expression. See here: https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html"
  type        = string
  default     = "15 minutes"
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

variable "partner_image_buckets" {
  description = "Names and arns of s3 buckets to consider as inputs to HMA. All images uploaded to these buckets will be processed by the hasher"
  type = list(object({
    name   = string
    arn    = string
    params = map(string)
  }))
  default = []
  # Ensure only correct params are used
  validation {
    condition = alltrue(
      [
        for partner_bucket in var.partner_image_buckets :
        alltrue(
          [
            for param_key in keys(partner_bucket.params) :
            # 'prefix' is the prefered term but we also accept 'folder' or 'path'. All these options are processed in the same way
            # similarly, 'suffix' is the prefered term but we also accept 'extension'
            param_key == "prefix" || param_key == "folder" || param_key == "path" || param_key == "suffix" || param_key == "extension"
          ]
        )
      ]
    )

    error_message = "The only accepted params are 'prefix' to specify a prefix/folder/path string where only uploads with that prefix should be sent to HMA and 'suffix' to restrict uploads to only files with a specific extension."
  }
}
variable "enable_partner_upload_notification" {
  description = "Enable the upload notfication of partner buckets if given."
  type        = bool
  default     = false
}

variable "integration_api_access_tokens" {
  description = "Access tokens checked for in authorizer api as an alternative to cognito user tokens."
  type        = list(string)
  sensitive   = true
  default     = []
}

variable "api_in_vpc" {
  description = "Should the API gateway used with HMA be made private behind a VPC. (Either way API will also require authorization)"
  type        = bool
}

variable "vpc_id" {
  description = "vpc that locks down the API and UI to the specfic vpc_subnets and security_groups. Required if api_in_vpc = true. Note VPC must be in the same region that HMA is deployed in."
  type        = string
  default     = ""
}

variable "vpc_subnets" {
  description = "Subnet ids of the vpc given in for vpc_id. Required if api_in_vpc = true"
  type        = list(string)
  default     = []
}

variable "security_groups" {
  description = "Security group ids to be used with the vpc given in for vpc_id. Required if api_in_vpc = true"
  type        = list(string)
  default     = []
}

variable "create_submit_event_sns_topic_and_handler" {
  description = "Enable alternative submit flow that accepts submission via a sns topic (arn of which is provided in outputs) instead of the API endpoints."
  type        = bool
  default     = false
}

variable "deadletterqueue_message_retention_seconds" {
  description = "Number of second messages should stay in dead letter queue after a repeated failure."
  type        = number
  default     = 604800
}
