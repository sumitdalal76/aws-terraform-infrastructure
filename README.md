# AWS Infrastructure Project

This project contains a modular Infrastructure as Code (IaC) implementation using Terraform with GitHub Actions CI pipeline.

## Project Structure

```
.
├── modules/
│   ├── networking/     # VPC, Subnets, Route Tables
│   ├── security/      # Security Groups
│   ├── loadbalancer/  # Application Load Balancer
│   └── dns/           # Route53 Configuration
├── environments/
│   └── prod/          # Production Environment
└── .github/
    └── workflows/     # CI Pipeline Configuration
```

## Infrastructure Components

- VPC with public and private subnets
- Route Tables for each subnet type
- Security Group for web traffic
- Application Load Balancer with HTTP to HTTPS redirect
- Route53 hosted zone with CNAME record

## Prerequisites

- AWS CLI configured with appropriate credentials
- Terraform >= 1.0.0
- S3 bucket for Terraform state
- GitHub repository secrets configured:
  - AWS_ACCESS_KEY_ID
  - AWS_SECRET_ACCESS_KEY

## CI/CD Pipeline

The GitHub Actions workflow:
1. Runs on push to main and pull requests
2. Formats and validates Terraform code
3. Plans changes on pull requests
4. Applies changes when merged to main

## Usage

1. Configure AWS credentials and S3 backend
2. Create `terraform.tfvars` in the environment directory:

```hcl
domain_name     = "example.com"
certificate_arn = "arn:aws:acm:region:account:certificate/cert-id"
```

3. Push to GitHub to trigger the CI pipeline

## Security Considerations

- HTTPS redirect enabled
- Private subnets isolated
- Least privilege IAM roles
- State file stored in S3

## Maintenance

- Regular provider updates
- Security patch application
- Infrastructure monitoring
- State file backup