output "alb_sg_id" {
  description = "Security Group ID for the Application Load Balancer and web instances"
  value       = aws_security_group.web.id
}