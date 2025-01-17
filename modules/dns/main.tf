#resource "aws_route53_zone" "main" {
#  name = var.domain_name
#
#  tags = {
#    Name = "${var.project_name}-zone"
#  }
#}

#resource "aws_route53_record" "www" {
#  zone_id = aws_route53_zone.main.zone_id
#  name    = "www.${var.domain_name}"
#  type    = "CNAME"
#  ttl     = "300"
#  records = [var.alb_dns_name]
#}