# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

variable "hma_lambda_docker_uri" {
  type = string
  description = "The URI for the docker image to use for the hma lambdas"
}

variable "prefix" {
  description = "Prefix to use for resource names"
  type = string
  default = "hma"
}
