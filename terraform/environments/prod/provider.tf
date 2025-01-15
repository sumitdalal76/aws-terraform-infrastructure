terraform {
  required_version = ">= 1.0.0"

  backend "s3" {
    bucket         = "your-terraform-state-bucket"
    key            = "prod/terraform.tfstate"
    region         = "us-west-2"
    dynamodb_table = "terraform-state-locks"
    encrypt        = true
  }
} 