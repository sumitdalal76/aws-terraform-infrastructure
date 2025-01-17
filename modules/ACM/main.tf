# Certificate request
resource "aws_acm_certificate" "main" {
  provider          = aws.us-east-1  # ACM certificate must be in us-east-1 for ALB
  domain_name       = var.domain_name
  validation_method = "DNS"

  tags = {
    Name        = "${var.project_name}-certificate"
    Environment = var.environment
  }

  lifecycle {
    create_before_destroy = true
  }
}

# DNS records for certificate validation
resource "aws_route53_record" "cert_validation" {
  provider = aws.us-east-1
  for_each = {
    for dvo in aws_acm_certificate.main.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = var.zone_id
}

# Certificate validation
resource "aws_acm_certificate_validation" "main" {
  provider                = aws.us-east-1
  certificate_arn         = aws_acm_certificate.main.arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
}