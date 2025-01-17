variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "security_group_id" {
  description = "ID of the security group"
  type        = string
}

variable "public_subnet_ids" {
  description = "IDs of public subnets"
  type        = list(string)
}

#variable "certificate_arn" {
#  description = "ARN of SSL certificate"
#  type        = string
#}