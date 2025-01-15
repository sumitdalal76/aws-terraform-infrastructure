module "infrastructure" {
  source = "../../"  # This points to the root terraform directory

  environment         = "prod"
  aws_region         = "us-west-2"
  vpc_cidr           = "10.0.0.0/16"
  availability_zones = ["us-west-2a", "us-west-2b"]
  domain_name        = "prod.yourdomain.com"
  certificate_arn    = "arn:aws:acm:region:account:certificate/prod-certificate-id"
} 