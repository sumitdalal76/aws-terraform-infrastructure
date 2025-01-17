resource "aws_route53_zone" "main" {
  name = var.domain_name

  tags = {
    Name        = "${var.project_name}-zone"
    Environment = var.environment
  }
}

resource "aws_route53_record" "alb" {
  zone_id = var.zone_id
  name    = var.domain_name
  type    = "CNAME"
  ttl     = "300"
  records = [var.alb_dns_name]
}