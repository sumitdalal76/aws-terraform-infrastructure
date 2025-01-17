#output "alb_dns_name" {
#  description = "DNS name of the load balancer"
#  value       = aws_lb.main.dns_name
#}

output "alb_arn" {
  description = "ARN of the load balancer"
  value       = aws_lb.main.arn
}