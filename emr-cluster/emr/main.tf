terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = ">= 5.44" }
  }
}

# Use deafult vpc 
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# Choose subnet id
locals {
  subnet_id = var.default_subnet_id != "" ? var.default_subnet_id : data.aws_subnets.default.ids[0]
}

# Cluster nodes security group
resource "aws_security_group" "sg_emr_cluster" {
  name        = "allow_tls_sg_emr_cluster"
  description = "Allow TLS inbound traffic and all outbound traffic"
  vpc_id      = data.aws_vpc.default.id
}

resource "aws_vpc_security_group_egress_rule" "sg_emr_cluster" {
  security_group_id = aws_security_group.sg_emr_cluster.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

# Log bucket
resource "aws_s3_bucket" "logs" {
  bucket        = "${var.cluster_name}-logs"
  force_destroy = true
}

# EMR service role 
data "aws_iam_policy_document" "emr_service_trust" {
  statement {
    actions = ["sts:AssumeRole"]
    principals { 
        type = "Service" 
        identifiers = ["elasticmapreduce.amazonaws.com"] 
    }
  }
}

resource "aws_iam_role" "emr_service_role" {
  name = "${var.cluster_name}-emr-role"
  assume_role_policy = jsonencode({
    Statement = [{
      Effect = "Allow",
      Principal = { Service = "elasticmapreduce.amazonaws.com" },
      Action   = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "emr_service_managed" {
  role       = aws_iam_role.emr_service_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonElasticMapReduceRole"
}

# EC2 role with SSM
resource "aws_iam_role" "emr_ec2" {
  name = "${var.cluster_name}-emr-ec2-ssm-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = { Service = "ec2.amazonaws.com" },
      Action   = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "emr_ec2_managed" {
  role       = aws_iam_role.emr_ec2.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonElasticMapReduceforEC2Role"
}

resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.emr_ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "emr_ec2_profile" {
  name = "${var.cluster_name}-ec2-profile"
  role = aws_iam_role.emr_ec2.name
}

# EMR cluster using TF registry module
module "cluster" {
  source  = "terraform-aws-modules/emr/aws"
  version = "~> 2.4"

  name          = var.cluster_name
  release_label = var.release_label
  applications  = ["Hadoop", "Spark"]

  create_service_iam_role = false
  service_iam_role_arn    = aws_iam_role.emr_service_role.arn

  create_iam_instance_profile = false
  iam_instance_profile_name   = aws_iam_instance_profile.emr_ec2_profile.name

  ec2_attributes = {
    subnet_id                         = local.subnet_id
    instance_profile                  = aws_iam_instance_profile.emr_ec2_profile.name
    additional_master_security_groups = aws_security_group.sg_emr_cluster.id
    additional_slave_security_groups  = aws_security_group.sg_emr_cluster.id
  }

  master_instance_group = {
    instance_type  = var.master_instance_type
    instance_count = 1
  }

  core_instance_group = {
    instance_type  = var.core_instance_type
    instance_count = 2
  }

  is_private_cluster = false
  vpc_id = data.aws_vpc.default.id

  log_uri = "s3://${aws_s3_bucket.logs.bucket}/logs/"
}

# Get master node instance ID for SSM conection
data "aws_instances" "master_group" {
  instance_tags = {
    "aws:elasticmapreduce:job-flow-id"       = module.cluster.cluster_id
    "aws:elasticmapreduce:instance-group-role" = "MASTER"
  }
  filter { 
    name = "instance-state-name"
    values = ["pending", "running"] 
  }
  depends_on = [module.cluster]
}

# Fleet-style tag
data "aws_instances" "master_fleet" {
  instance_tags = {
    "aws:elasticmapreduce:job-flow-id"       = module.cluster.cluster_id
    "aws:elasticmapreduce:instance-fleet-type" = "MASTER"
  }
  filter { 
    name = "instance-state-name"
    values = ["pending", "running"] 
    }
  depends_on = [module.cluster]
}

locals {
  master_ids = length(data.aws_instances.master_group.ids) > 0 ? data.aws_instances.master_group.ids : data.aws_instances.master_fleet.ids
}