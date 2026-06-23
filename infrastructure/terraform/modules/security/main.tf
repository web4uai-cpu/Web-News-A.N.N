##############################################################################
# A.N.N. Security Hardening
# WAF, DDoS protection, secret rotation, mTLS preparation
##############################################################################

variable "project_name" { type = string }
variable "environment" { type = string }
variable "alb_arn" { type = string }

# ── WAF (Web Application Firewall) ──────────────────────

resource "aws_wafv2_web_acl" "main" {
  name        = "${var.project_name}-${var.environment}-waf"
  description = "A.N.N. WAF with OWASP Core Rule Set"
  scope       = "REGIONAL"

  default_action { allow {} }

  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 1
    override_action { none {} }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "CommonRuleSet"
    }
  }

  rule {
    name     = "AWSManagedRulesSQLiRuleSet"
    priority = 2
    override_action { none {} }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesSQLiRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "SQLiRuleSet"
    }
  }

  rule {
    name     = "RateLimitRule"
    priority = 3
    action { block {} }

    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimitRule"
    }
  }

  visibility_config {
    sampled_requests_enabled   = true
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.project_name}-${var.environment}-waf"
  }
}

resource "aws_wafv2_web_acl_association" "alb" {
  resource_arn = var.alb_arn
  web_acl_arn  = aws_wafv2_web_acl.main.arn
}

# ── Secret Rotation ─────────────────────────────────────

resource "aws_secretsmanager_secret" "api_keys" {
  name = "${var.project_name}-${var.environment}-api-keys"

  tags = { AutoRotate = "true" }
}

resource "aws_secretsmanager_secret_rotation" "api_keys" {
  secret_id           = aws_secretsmanager_secret.api_keys.id
  rotation_lambda_arn = aws_lambda_function.secret_rotator.arn

  rotation_rules {
    automatically_after_days = 90
  }
}

resource "aws_lambda_function" "secret_rotator" {
  function_name = "${var.project_name}-${var.environment}-secret-rotator"
  runtime       = "python3.12"
  handler       = "index.handler"
  filename      = "${path.module}/lambda/secret_rotator.zip"
  role          = aws_iam_role.lambda_rotator.arn
  timeout       = 60

  environment {
    variables = {
      PROJECT     = var.project_name
      ENVIRONMENT = var.environment
    }
  }
}

resource "aws_iam_role" "lambda_rotator" {
  name = "${var.project_name}-${var.environment}-secret-rotator"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_rotator.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# ── Shield Advanced (DDoS) ──────────────────────────────

resource "aws_shield_protection" "alb" {
  count        = var.environment == "production" ? 1 : 0
  name         = "${var.project_name}-alb-protection"
  resource_arn = var.alb_arn
}

output "waf_acl_arn" { value = aws_wafv2_web_acl.main.arn }
