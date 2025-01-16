terraform {
  required_version = ">= 1.0.0"

  backend "s3" {
    bucket         = "772102554033-stage-terraform-state"
    key            = "staging/terraform.tfstate"
    region         = "ca-central-1"
    dynamodb_table = "terraform-state-locks"
    encrypt        = true
  }
} 