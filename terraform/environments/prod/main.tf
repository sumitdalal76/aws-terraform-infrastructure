module "infrastructure" {
  source = "../../modules"

  environment         = var.environment
  aws_region         = var.aws_region
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
}