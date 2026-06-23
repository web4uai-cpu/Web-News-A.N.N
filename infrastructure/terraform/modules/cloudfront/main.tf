resource "aws_cloudfront_origin_access_identity" "media" {
  comment = "A.N.N. media bucket access for ${var.environment}"
}

data "aws_iam_policy_document" "s3_cloudfront" {
  statement {
    actions   = ["s3:GetObject"]
    resources = ["${var.media_bucket_arn}/*"]
    principals {
      type        = "AWS"
      identifiers = [aws_cloudfront_origin_access_identity.media.iam_arn]
    }
  }
}

resource "aws_s3_bucket_policy" "media" {
  bucket = var.media_bucket_name
  policy = data.aws_iam_policy_document.s3_cloudfront.json
}

resource "aws_cloudfront_distribution" "media" {
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = ""
  price_class         = "PriceClass_200"
  comment             = "A.N.N. Media CDN - ${var.environment}"

  aliases = var.domain_name != "" ? [var.domain_name] : []

  origin {
    domain_name = "${var.media_bucket_name}.s3.amazonaws.com"
    origin_id   = "S3-${var.media_bucket_name}"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.media.cloudfront_access_identity_path
    }
  }

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${var.media_bucket_name}"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    forwarded_values {
      query_string = false
      cookies { forward = "none" }
    }

    min_ttl     = 0
    default_ttl = 86400
    max_ttl     = 31536000
  }

  ordered_cache_behavior {
    path_pattern           = "/audio/*"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${var.media_bucket_name}"
    viewer_protocol_policy = "redirect-to-https"
    compress               = false

    forwarded_values {
      query_string = true
      cookies { forward = "none" }
    }

    min_ttl     = 3600
    default_ttl = 604800
    max_ttl     = 2592000
  }

  ordered_cache_behavior {
    path_pattern           = "/video/*"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${var.media_bucket_name}"
    viewer_protocol_policy = "redirect-to-https"
    compress               = false

    forwarded_values {
      query_string = true
      cookies { forward = "none" }
    }

    min_ttl     = 3600
    default_ttl = 604800
    max_ttl     = 2592000
  }

  restrictions {
    geo_restriction { restriction_type = "none" }
  }

  viewer_certificate {
    cloudfront_default_certificate = var.acm_certificate == ""
    acm_certificate_arn            = var.acm_certificate != "" ? var.acm_certificate : null
    ssl_support_method             = var.acm_certificate != "" ? "sni-only" : null
    minimum_protocol_version       = "TLSv1.2_2021"
  }
}

variable "project_name" { type = string }
variable "environment" { type = string }
variable "media_bucket_arn" { type = string }
variable "media_bucket_name" { type = string }
variable "domain_name" { type = string }
variable "acm_certificate" { type = string }

output "distribution_domain" { value = aws_cloudfront_distribution.media.domain_name }
output "distribution_id" { value = aws_cloudfront_distribution.media.id }
