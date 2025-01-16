module "infrastructure" {
  source = "../../"  # This points to the root terraform directory

  environment         = "prod"
  aws_region         = "ca-central-1"
  vpc_cidr           = "10.0.0.0/16"
  availability_zones = ["ca-central-1a", "ca-central-1b"]
  domain_name        = "prod.yourdomain.com"
  certificate_arn    = "arn:aws:acm:region:account:certificate/prod-certificate-id"
} 