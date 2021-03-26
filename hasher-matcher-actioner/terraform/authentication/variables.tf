# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

variable "prefix" {
  description = "Prefix to use for resource names"
  type        = string
}

variable "organization" {
  description = "The name / acronym to use for resource names that must be globally unique (use only lower case alpha a-z, and, optionally, hyphens)"
  type        = string
}

variable "use_cloudfront_distribution_url" {
  description = "Indicates whether the callback and sign out urls should be set to one based on the cloudfront distribution domain name"
  type        = bool
}

variable "cloudfront_distribution_url" {
  description = "The url based on the cloudfront distribution domain name"
  type        = string
}
