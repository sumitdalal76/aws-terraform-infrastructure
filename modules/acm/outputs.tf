output "certificate_arn" {
  value = aws_acm_certificate_validation.cert_validation.certificate_arn
}

output "domain_name" {
  description = "Domain name the certificate is issued for"
  value       = var.domain_name
}