terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket         = "772102554033-prod-terraform-state"
    key            = "infrastructure/terraform.tfstate"
    region         = "ca-central-1"
    dynamodb_table = "terraform-state-locks"
  }
}

provider "aws" {
  region = var.aws_region
}

# Provider for us-east-1 (required for ACM certificates used with ALB)
provider "aws" {
  alias  = "us-east-1"
  region = "us-east-1"
}

module "networking" {
  source = "../../modules/networking"

  vpc_cidr             = var.vpc_cidr
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  project_name         = var.project_name
  environment          = var.environment
}

module "security" {
  source = "../../modules/security"

  project_name = var.project_name
  environment  = var.environment
  vpc_id       = module.networking.vpc_id
}

# DNS module
module "dns" {
  source = "../../modules/dns"

  project_name = var.project_name
  domain_name  = var.domain_name
  environment  = var.environment
  alb_dns_name = ""  # Empty for initial zone creation
  zone_id      = ""  # Empty for initial zone creation
}

# ACM module
module "acm" {
  source = "../../modules/acm"
  providers = {
    aws.us-east-1 = aws.us-east-1
  }
  
  domain_name  = var.domain_name
  project_name = var.project_name
  environment  = var.environment
  zone_id      = module.dns.zone_id

  depends_on = [module.dns]
}

# Loadbalancer module
module "loadbalancer" {
  source = "../../modules/loadbalancer"
  
  project_name      = var.project_name
  environment       = var.environment
  vpc_id           = module.networking.vpc_id
  public_subnet_ids = module.networking.public_subnet_ids
  security_group_id = module.security.alb_sg_id
  certificate_arn   = module.acm.certificate_arn

  depends_on = [module.acm]
}

# Update DNS after load balancer is created
module "dns_records" {
  source = "../../modules/dns"

  project_name  = var.project_name
  domain_name   = var.domain_name
  environment   = var.environment
  alb_dns_name  = module.loadbalancer.alb_dns_name
  zone_id       = module.dns.zone_id

  depends_on = [module.loadbalancer]
}

module "ec2" {
  source = "../../modules/ec2"

  project_name      = var.project_name
  environment       = var.environment
  ami_id           = var.ami_id
  subnet_id        = module.networking.public_subnet_ids[0]
  security_group_id = module.security.alb_sg_id
  target_group_arn = module.loadbalancer.target_group_arn

  depends_on = [module.networking, module.security, module.loadbalancer]
}