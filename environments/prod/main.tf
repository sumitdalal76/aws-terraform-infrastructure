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

  vpc_cidr            = var.vpc_cidr
  public_subnet_cidrs = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  project_name        = var.project_name
  environment         = var.environment
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

  project_name  = var.project_name
  domain_name   = var.domain_name
  alb_dns_name  = module.loadbalancer.alb_dns_name
  environment   = var.environment
}

# ACM module
module "acm" {
  source = "../../modules/acm"
  providers = {
    aws = aws.us-east-1
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
  security_group_id = module.security.security_group_id
  public_subnet_ids = module.networking.public_subnet_ids
  vpc_id            = module.networking.vpc_id
  environment       = var.environment
  certificate_arn   = var.certificate_arn
}

module "ec2" {
  source = "../../modules/ec2"

  project_name      = var.project_name
  environment       = var.environment
  ami_id           = var.ami_id  # Ubuntu 20.04 AMI ID
  subnet_id        = module.networking.public_subnet_ids[0]  # First public subnet
  security_group_id = module.security.web_sg_id
  target_group_arn = module.loadbalancer.target_group_arn

  depends_on = [module.networking, module.security, module.loadbalancer]
}