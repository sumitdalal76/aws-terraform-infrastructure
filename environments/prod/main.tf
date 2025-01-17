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

module "networking" {
  source = "../../modules/networking"

  vpc_cidr            = var.vpc_cidr
  public_subnet_cidrs = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  project_name        = var.project_name
}

module "security" {
  source = "../../modules/security"

  project_name = var.project_name
  vpc_id       = module.networking.vpc_id
}

module "loadbalancer" {
  source = "../../modules/loadbalancer"

  project_name      = var.project_name
  security_group_id = module.security.security_group_id
  public_subnet_ids = module.networking.public_subnet_ids
  vpc_id            = module.networking.vpc_id
#  certificate_arn   = var.certificate_arn
}

#module "dns" {
#  source = "../../modules/dns"

#  project_name  = var.project_name
#  domain_name   = var.domain_name
#  alb_dns_name  = module.loadbalancer.alb_dns_name
#}