output "vpc_id" {
  description = "ID of the VPC"
  value       = module.networking.vpc_id
}

output "public_subnet_ids" {
  description = "IDs of public subnets"
  value       = module.networking.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs of private subnets"
  value       = module.networking.private_subnet_ids
}

output "certificate_arn" {
  description = "ACM Certificate ARN"
  value       = module.acm.certificate_arn
}

output "summary" {
  description = "Application Access Information"
  value = <<EOF

=============================================================
  Application will be accessible at: https://${var.domain_name}
=============================================================
EOF
}