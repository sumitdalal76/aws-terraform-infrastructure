variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "domain_name" {
  description = "Domain name for the hosted zone"
  type        = string
}

variable "environment" {
  description = "Environment (e.g., prod, dev, staging)"
  type        = string
}