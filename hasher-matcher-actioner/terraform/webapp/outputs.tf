# Copyright (c) Meta Platforms, Inc. and affiliates.

output "s3_bucket_name" {
  value = aws_s3_bucket.webapp.bucket
}

output "cloudfront_distribution_domain_name" {
  value = var.include_cloudfront_distribution ? aws_cloudfront_distribution.webapp[0].domain_name : "no-cloudfront-distribution"
}

output "ui_url" {
  value = aws_s3_bucket.webapp.website_endpoint
}
