variable "zone_id" {
  description = "The ID of the hosted zone"
  type        = string
}

variable "domain_name" {
  description = "Domain name for the record"
  type        = string
}

variable "alb_dns_name" {
  description = "ALB DNS name for CNAME record"
  type        = string
}