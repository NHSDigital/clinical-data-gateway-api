terraform {
  required_version = ">= 1.4.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Typically you'll set a different key per branch in CI (e.g. dev/preview/<branch>.tfstate)
  backend "s3" {
    bucket = "cds-cdg-dev-tfstate-900119715266"
    key    = "dev/preview/branch_name.tfstate"
    region = "eu-west-2"
  }
}

provider "aws" {
  region = "eu-west-2"
}
