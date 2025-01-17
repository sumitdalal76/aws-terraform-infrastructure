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
ami_id = "ami-0ea18256de20ecdfc"  # Ubuntu 20.04 LTS in ca-central-1

apex_domain = "devopslab.buzz"
domain_name = "myapp-prod.devopslab.buzz"
porkbun_api_key = "pk1_d0c9d2b69a5f3ae22049aa93d5733399906db8d29572a9cae34bbd39f16d2bec"
porkbun_secret_key = "sk1_5ef1576233ff6ceeed330b0e8d055530950a5a2e83ea6bbc69a68c9ef0676142"