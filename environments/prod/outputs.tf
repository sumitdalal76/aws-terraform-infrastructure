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

#output "alb_dns_name" {
#  description = "DNS name of the load balancer"
#  value       = module.loadbalancer.alb_dns_name
#}

#output "route53_nameservers" {
#  description = "Nameservers for the Route53 zone"
#  value       = module.dns.route53_nameservers
#}