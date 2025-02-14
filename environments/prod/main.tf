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

module "dns" {
  source = "../../modules/dns"

  project_name = var.project_name
  apex_domain  = var.apex_domain
  environment  = var.environment
}

module "acm" {
  source = "../../modules/acm"

  domain_name  = var.domain_name
  project_name = var.project_name
  environment  = var.environment
  zone_id      = module.dns.zone_id

  depends_on = [null_resource.update_nameservers]
}

module "loadbalancer" {
  source = "../../modules/loadbalancer"

  project_name      = var.project_name
  environment       = var.environment
  vpc_id            = module.networking.vpc_id
  public_subnet_ids = module.networking.public_subnet_ids
  security_group_id = module.security.alb_sg_id
  certificate_arn   = module.acm.certificate_arn
  zone_id           = module.dns.zone_id
  domain_name       = var.domain_name

  depends_on = [module.acm]
}

module "ec2" {
  source = "../../modules/ec2"

  project_name      = var.project_name
  environment       = var.environment
  ami_id            = var.ami_id
  subnet_id         = module.networking.public_subnet_ids[0]
  security_group_id = module.security.alb_sg_id
  target_group_arn  = module.loadbalancer.target_group_arn

  depends_on = [module.networking, module.security, module.loadbalancer]
}

data "aws_route53_zone" "selected" {
  name       = var.apex_domain
  depends_on = [module.dns]
}

resource "null_resource" "update_nameservers" {
  triggers = {
    zone_id = module.dns.zone_id
  }

  provisioner "local-exec" {
    command = "python3 ../../scripts/update_nameservers.py ${var.apex_domain} ${var.porkbun_api_key} ${var.porkbun_secret_key} ${join(" ", data.aws_route53_zone.selected.name_servers)}"
  }

  depends_on = [module.dns]
}