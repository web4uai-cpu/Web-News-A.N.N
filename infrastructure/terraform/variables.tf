variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "ann"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "staging"
  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "Environment must be staging or production."
  }
}

variable "aws_region" {
  description = "Primary AWS region"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "az_count" {
  description = "Number of availability zones"
  type        = number
  default     = 3
}

# ── EKS ──────────────────────────────────────────────────

variable "eks_node_instance_type" {
  description = "EC2 instance type for EKS worker nodes"
  type        = string
  default     = "t3.medium"
}

variable "eks_node_desired_count" {
  type    = number
  default = 2
}

variable "eks_node_min_count" {
  type    = number
  default = 1
}

variable "eks_node_max_count" {
  type    = number
  default = 5
}

# ── RDS ──────────────────────────────────────────────────

variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.medium"
}

variable "db_name" {
  type    = string
  default = "ann_db"
}

variable "db_username" {
  type      = string
  default   = "ann_admin"
  sensitive = true
}

# ── ElastiCache ──────────────────────────────────────────

variable "redis_node_type" {
  type    = string
  default = "cache.t3.small"
}

# ── CDN ──────────────────────────────────────────────────

variable "cdn_domain_name" {
  description = "Custom domain for CloudFront distribution"
  type        = string
  default     = ""
}

variable "acm_certificate_arn" {
  description = "ACM certificate ARN for CloudFront HTTPS"
  type        = string
  default     = ""
}
