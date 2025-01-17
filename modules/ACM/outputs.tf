output "certificate_arn" {
  description = "ARN of the created certificate"
  value       = aws_acm_certificate.main.arn
}

output "domain_name" {
  description = "Domain name the certificate is issued for"
  value       = var.domain_name
}