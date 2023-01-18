# Copyright (c) Meta Platforms, Inc. and affiliates.

variable "prefix" {
  description = "Prefix to use for resource names"
  type        = string
}

variable "organization" {
  description = "The name / acronym to use for resource names that must be globally unique (use only lower case alpha a-z, and, optionally, hyphens)"
  type        = string
}

variable "additional_tags" {
  description = "Additional resource tags"
  type        = map(string)
  default     = {}
}

variable "include_cloudfront_distribution" {
  description = "Indicates whether a CloudFront distribution is included"
  type        = bool
}
