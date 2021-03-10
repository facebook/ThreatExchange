# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

#terraform {
#  required_providers {
#    aws = "~> 3.0"
#  }
#}

#provider "aws" {
#  region  = var.region
#  profile = var.profile
#}

resource "aws_s3_bucket" "webapp_bucket" {
  bucket = "${var.prefix}-webapp"
  acl           = "public-read"
  tags = merge(
    var.additional_tags,
    {
      Name = "WebappBucket"
    }
  )
  website {
    index_document = "index.html"
    error_document = "index.html"
  }
  provisioner "local-exec" {
    command = "npm run build"
    working_dir = "../webapp"
  }
  provisioner "local-exec" {
    command = "aws s3 sync ../webapp/build s3://${var.prefix}-webapp --acl public-read"
  }
  # For development, this makes cleanup easier
  # If deploying for real, this should not be used
  # Could also be set with a variable
  force_destroy = true
}
