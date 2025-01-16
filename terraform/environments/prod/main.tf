terraform {
  required_version = ">= 1.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }

  backend "s3" {
    bucket         = "772102554033-terraform-state"
    key            = "terraform.tfstate"
    region         = "ca-central-1"
    dynamodb_table = "terraform-state-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region
}

module "infrastructure" {
  source = "../../"  # This points to the root terraform directory

  environment         = "prod"
  aws_region         = "us-west-2"
  vpc_cidr           = "10.0.0.0/16"
  availability_zones = ["us-west-2a", "us-west-2b"]
  domain_name        = "prod.yourdomain.com"
  certificate_arn    = "arn:aws:acm:region:account:certificate/prod-certificate-id"
} 