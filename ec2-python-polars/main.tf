## PYTHON - POLARS ON EC2

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"

  default_tags {
    tags = {
      Topic = "terraform"
      Owner = "gajeto"
    }
  }
}


module "ec2" {
  source = "./ec2"
  instance_type = "t2.micro"
  user_data = filebase64("./scripts/user_data.sh")
}

output "instance_public_ip" {
  value = module.ec2.instance_public_ip
}

output "instance_profile_ssm_name" {
  value = module.ec2.instance_profile_ssm_name
}

output "instance_ID" {
  value = module.ec2.instance_ID
}