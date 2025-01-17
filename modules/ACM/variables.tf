variable "domain_name" {
  description = "Domain name for the certificate"
  type        = string
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name for resource tagging"
  type        = string
}

variable "zone_id" {
  description = "Route53 zone ID for DNS validation"
  type        = string
}