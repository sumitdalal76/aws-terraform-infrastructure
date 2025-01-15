module "infrastructure" {
  source = "../../"  # This points to the root terraform directory

  environment         = "staging"
  aws_region         = "us-west-2"
  vpc_cidr           = "10.1.0.0/16"  # Different CIDR for staging
  availability_zones = ["us-west-2a", "us-west-2b"]
  domain_name        = "staging.yourdomain.com"
  certificate_arn    = "arn:aws:acm:region:account:certificate/staging-certificate-id"
} 