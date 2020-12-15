terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

variable "hma_lambda_docker_uri" {
  type = string
  description = "The URI for the docker image to use for the hma lambdas"
}

resource "aws_s3_bucket" "hashing_bucket" {
  acl = "private"
  versioning {
    enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "hashing_bucket" {
  bucket = aws_s3_bucket.hashing_bucket.id
   
  block_public_acls = true
  block_public_policy = true
  ignore_public_acls = true
  restrict_public_buckets = true
}

resource "aws_iam_role" "hma_lambda_role" {
  name = "hma_lambda_role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
  EOF
}

resource "aws_lambda_function" "pdq_hasher_lambda" {
  function_name = "pdq_hasher_lambda"
  package_type = "Image"
  role = aws_iam_role.hma_lambda_role.arn
  image_uri = var.hma_lambda_docker_uri
  image_config {
    command = [ "pdq_hasher.lambda_handler" ]
  }
}

resource "aws_lambda_function" "pdq_matcher_lambda" {
  function_name = "pdq_matcher_lambda"
  package_type = "Image"
  role = aws_iam_role.hma_lambda_role.arn
  image_uri = var.hma_lambda_docker_uri
  image_config {
    command = [ "pdq_matcher.lambda_handler" ]
  }
}
