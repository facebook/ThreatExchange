# Copyright (c) Meta Platforms, Inc. and affiliates.

resource "aws_s3_bucket" "webapp" {
  bucket = "${var.organization}-${var.prefix}-hma-webapp"
  acl    = var.include_cloudfront_distribution ? "private" : "public-read"
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
  # For development, this makes cleanup easier
  # If deploying for real, this should not be used
  # Could also be set with a variable
  force_destroy = true
}


resource "aws_cloudfront_origin_access_identity" "webapp" {
  count   = var.include_cloudfront_distribution ? 1 : 0
  comment = "OAI for the webapp to access the s3 site"
}

data "aws_iam_policy_document" "s3_policy" {
  count = var.include_cloudfront_distribution ? 1 : 0
  statement {
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.webapp.arn}/*"]

    principals {
      type        = "AWS"
      identifiers = [aws_cloudfront_origin_access_identity.webapp[0].iam_arn]
    }
  }
}

resource "aws_s3_bucket_policy" "webapp" {
  count  = var.include_cloudfront_distribution ? 1 : 0
  bucket = aws_s3_bucket.webapp.id
  policy = data.aws_iam_policy_document.s3_policy[0].json
}


resource "aws_cloudfront_distribution" "webapp" {
  count = var.include_cloudfront_distribution ? 1 : 0

  default_root_object = "index.html"
  enabled             = true
  http_version        = "http2"
  is_ipv6_enabled     = true

  origin {
    origin_id   = "${var.organization}-${var.prefix}-hma-webapp-origin"
    domain_name = aws_s3_bucket.webapp.bucket_domain_name

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.webapp[0].cloudfront_access_identity_path
    }
  }

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true
    default_ttl            = 300
    max_ttl                = 1200
    min_ttl                = 0
    target_origin_id       = "${var.organization}-${var.prefix}-hma-webapp-origin"
    viewer_protocol_policy = "redirect-to-https"
    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
  }

  custom_error_response {
    error_caching_min_ttl = 3000
    error_code            = 404
    response_code         = 200
    response_page_path    = "/index.html"
  }
  custom_error_response {
    error_caching_min_ttl = 3000
    error_code            = 403
    response_code         = 200
    response_page_path    = "/index.html"
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
