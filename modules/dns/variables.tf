variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "apex_domain" {
  description = "Domain name for the hosted zone"
  type        = string
}

variable "environment" {
  description = "Environment (e.g., prod, dev, staging)"
  type        = string
}