module "infrastructure" {
  source = "../../"

  environment         = "staging"
  aws_region         = "ca-central-1"
  vpc_cidr           = "10.1.0.0/16"  # Different CIDR for staging
  availability_zones = ["ca-central-1a", "ca-central-1b"]
  domain_name        = "staging.yourdomain.com"
  certificate_arn    = "arn:aws:acm:region:account:certificate/staging-certificate-id"
} 