# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

variable "prefix" {
  description = "Prefix to use for resource names"
  type        = string
}

variable "additional_tags" {
  description = "Additional resource tags"
  type        = map(string)
}

