aws_region = "ca-central-1"
project_name = "prod"
environment = "prod"
vpc_cidr = "10.0.0.0/16"
public_subnet_cidrs = [
  "10.0.1.0/24",
  "10.0.2.0/24"
]
private_subnet_cidrs = [
  "10.0.3.0/24",
  "10.0.4.0/24"
]

domain_name = "myapp-prod.com"
ami_id = "ami-0ea18256de20ecdfc"  # Ubuntu 20.04 LTS in ca-central-1