# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

variable "prefix" {
  description = "Prefix to use for resource names"
  type        = string
  default     = "hma"
}

variable "additional_tags" {
  description = "Additional resource tags. Will be applied to ALL resources created."
  type        = map(string)
  default     = {}
}
