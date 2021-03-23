# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

resource "aws_s3_bucket" "webapp" {
  bucket = "${var.prefix}-hma-webapp"
  acl    = "public-read"
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
    command     = "npm install --silent"
    working_dir = "../webapp"
  }
  provisioner "local-exec" {
    command     = "npm run build"
    working_dir = "../webapp"
  }
  provisioner "local-exec" {
    command = "aws s3 sync ../webapp/build s3://${var.prefix}-hma-webapp --acl public-read"
  }
  # For development, this makes cleanup easier
  # If deploying for real, this should not be used
  # Could also be set with a variable
  force_destroy = true
}

resource "aws_cloudfront_distribution" "webapp" {
  count = var.include_cloudfront_distribution ? 1 : 0

  default_root_object = "index.html"
  enabled             = true
  http_version        = "http2"
  is_ipv6_enabled     = true

  origin {
    origin_id   = "${var.prefix}-hma-webapp-origin"
    domain_name = aws_s3_bucket.webapp.website_endpoint

    custom_origin_config {
      http_port              = "80"
      https_port             = "443"
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true
    default_ttl            = 300
    max_ttl                = 1200
    min_ttl                = 0
    target_origin_id       = "${var.prefix}-hma-webapp-origin"
    viewer_protocol_policy = "allow-all"
    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}
