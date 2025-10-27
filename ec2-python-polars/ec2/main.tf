# Create an IAM role that EC2 can assume and attach the policy and profile to add SSM permissionss
resource "aws_iam_role" "ec2_ssm" {
  name = "ec2-ssm-role-polars"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = { Service = "ec2.amazonaws.com" },
      Action   = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ec2_ssm_core" {
  role       = aws_iam_role.ec2_ssm.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# Give EC2 permission to read from S3 bucket data-task-5
resource "aws_iam_policy" "s3_read_app" {
  name        = "ec2-s3-read-data-task-5"
  description = "Allow EC2 to get app artifact from data-task-5 bucket"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = ["s3:GetObject"],
        Resource = "arn:aws:s3:::data-task-5/*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "s3_read_attach" {
  role       = aws_iam_role.ec2_ssm.name
  policy_arn = aws_iam_policy.s3_read_app.arn
}

resource "aws_iam_instance_profile" "ec2_ssm" {
  name = "ec2-ssm-instance-profile-polars"
  role = aws_iam_role.ec2_ssm.name
}

resource "aws_instance" "ec2_polars" {
  ami                         = data.aws_ami.ec2_polars.id
  instance_type               = var.instance_type
  security_groups             = [aws_security_group.ec2_polars.name]
  iam_instance_profile        = aws_iam_instance_profile.ec2_ssm.name
  user_data                   = var.user_data
  user_data_replace_on_change = true

  tags = {
    Name = "ec2_polars"
  }
}

# Provision an Amazon Linux 2023 AMI
data "aws_ami" "ec2_polars" {
  most_recent = true
  owners = ["amazon"]

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

}

# Create security group for the instance and egress rule
resource "aws_security_group" "ec2_polars" {
  name        = "allow_tls-polars"
  description = "Allow TLS inbound traffic and all outbound traffic"
}

resource "aws_vpc_security_group_egress_rule" "ec2_polars" {
  security_group_id = aws_security_group.ec2_polars.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

# Bucket for tests scipts in EC2
resource "aws_s3_bucket" "data-task-5" {
  bucket        = "data-task-5"
  force_destroy = true
}
