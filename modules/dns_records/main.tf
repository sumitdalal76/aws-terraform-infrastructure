# Create CNAME record for ALB
resource "aws_route53_record" "alb" {
  zone_id = var.zone_id
  name    = var.domain_name
  type    = "CNAME"
  ttl     = "300"
  records = [var.alb_dns_name]
}