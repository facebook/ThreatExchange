# Copyright (c) Meta Platforms, Inc. and affiliates.

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

variable "use_shared_user_pool" {
  description = "Indicates if the web app and api will use a shared user pool (generally true for developers / engineers sandbox environments, otherwise false)"
  type        = bool
}

variable "webapp_and_api_shared_user_pool_id" {
  description = "The id of the shared user pool. Used in conjunction with use_shared_user_pool set to true. Generate by running terraform init & apply from /authentication-shared."
  type        = string
}

variable "webapp_and_api_shared_user_pool_client_id" {
  description = "The id of the shared user pool app client. Used in conjunction with use_shared_user_pool set to true. Generate by running terraform init & apply from /authentication-shared."
  type        = string
}
