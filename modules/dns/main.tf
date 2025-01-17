# Create Route53 zone
resource "aws_route53_zone" "main" {
  name = var.apex_domain

  tags = {
    Name        = "${var.project_name}-zone"
    Environment = var.environment
  }
}