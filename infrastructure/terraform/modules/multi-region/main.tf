##############################################################################
# A.N.N. Multi-Region Deployment
# Provisions Route53 health checks and failover routing across regions.
##############################################################################

variable "project_name" { type = string }
variable "environment" { type = string }
variable "primary_region" { type = string }
variable "domain_name" { type = string }
variable "hosted_zone_id" { type = string }

variable "regions" {
  type = map(object({
    eks_endpoint     = string
    alb_dns_name     = string
    alb_zone_id      = string
    is_primary       = bool
  }))
}

resource "aws_route53_health_check" "region" {
  for_each = var.regions

  fqdn              = each.value.alb_dns_name
  port               = 443
  type               = "HTTPS"
  resource_path      = "/health"
  failure_threshold  = 3
  request_interval   = 10

  tags = {
    Name = "${var.project_name}-${var.environment}-${each.key}-health"
  }
}

resource "aws_route53_record" "primary" {
  for_each = { for k, v in var.regions : k => v if v.is_primary }

  zone_id = var.hosted_zone_id
  name    = "api.${var.domain_name}"
  type    = "A"

  alias {
    name                   = each.value.alb_dns_name
    zone_id                = each.value.alb_zone_id
    evaluate_target_health = true
  }

  set_identifier  = each.key
  health_check_id = aws_route53_health_check.region[each.key].id

  failover_routing_policy {
    type = "PRIMARY"
  }
}

resource "aws_route53_record" "secondary" {
  for_each = { for k, v in var.regions : k => v if !v.is_primary }

  zone_id = var.hosted_zone_id
  name    = "api.${var.domain_name}"
  type    = "A"

  alias {
    name                   = each.value.alb_dns_name
    zone_id                = each.value.alb_zone_id
    evaluate_target_health = true
  }

  set_identifier  = each.key
  health_check_id = aws_route53_health_check.region[each.key].id

  failover_routing_policy {
    type = "SECONDARY"
  }
}

resource "aws_route53_record" "latency" {
  for_each = var.regions

  zone_id = var.hosted_zone_id
  name    = "cdn.${var.domain_name}"
  type    = "A"

  alias {
    name                   = each.value.alb_dns_name
    zone_id                = each.value.alb_zone_id
    evaluate_target_health = true
  }

  set_identifier = each.key

  latency_routing_policy {
    region = each.key
  }
}

output "health_check_ids" {
  value = { for k, v in aws_route53_health_check.region : k => v.id }
}
