## SPARK CLUSTER ON EMR

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

module "emr" {
  source = "./emr"
  cluster_name = var.cluster_name
  release_label = var.release_label
  master_instance_type = var.master_instance_type
  core_instance_type = var.core_instance_type
  default_subnet_id = var.default_subnet_id
}

output "emr_cluster_id" {
  value = module.emr.cluster_id
}

output "emr_master_node_instance_id" {
  value = module.emr.master_node_instance_id
}

