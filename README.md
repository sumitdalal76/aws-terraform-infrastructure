# AWS Infrastructure Project

This project contains a modular Infrastructure as Code (IaC) implementation using Terraform with GitHub Actions CI/CD pipelines.

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
    └── workflows/     # CI/CD Pipeline Configurations
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

## GitHub Actions Workflows

### 1. Terraform CI/CD (terraform.yml)
Main deployment pipeline that:
- Runs on push to main and pull requests
- Formats and validates Terraform code
- Plans changes on pull requests
- Applies changes when merged to main
- Allows manual destroy via workflow dispatch

### 2. Terraform CI (terraform-ci.yml)
Continuous Integration workflow that:
- Validates code on pull requests
- Runs terraform fmt check
- Performs terraform plan
- Shows potential changes before merge

### 3. Terraform Deploy (terraform-deploy.yml)
Manual deployment workflow that:
- Triggered manually via workflow dispatch
- Allows selecting environment (prod)
- Runs plan and apply
- Useful for one-off deployments

### 4. Terraform Destroy (terraform-destroy.yml)
Infrastructure cleanup workflow that:
- Triggered manually via workflow dispatch
- Requires environment approval
- Destroys all resources in selected environment
- Use with caution!

### 5. AWS Inventory (aws-inventory.yml)
Resource tracking workflow that:
- Can be triggered manually
- Generates inventory of AWS resources:
  - VPCs and Networking
  - EC2 Instances
  - RDS Databases
  - Lambda Functions
  - DynamoDB Tables
  - S3 Buckets
- Saves inventory as workflow artifact

## Usage

1. Configure AWS credentials and S3 backend
2. Create `terraform.tfvars` in the environment directory:
```hcl
aws_region = "ca-central-1"
project_name = "prod"
vpc_cidr = "10.0.0.0/16"
public_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24"]
private_subnet_cidrs = ["10.0.3.0/24", "10.0.4.0/24"]
```

3. Push to GitHub to trigger CI/CD pipeline

4. For manual operations:
   - Use "Terraform Deploy" workflow for deployments
   - Use "Terraform Destroy" workflow for cleanup
   - Use "AWS Inventory" workflow to check resources

## Security Considerations

- HTTPS redirect enabled (Commented)
- Private subnets isolated
- Least privilege IAM roles
- State file stored in S3
- Environment approvals required for critical actions
- Terraform state lock file stored to dynamodb

## Maintenance

- Infrastructure monitoring
- State file backup