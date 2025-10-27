output "instance_public_ip" {
  value = aws_instance.ec2_polars.public_ip
}

output "instance_profile_ssm_name" {
  value = aws_iam_instance_profile.ec2_ssm.name
}

output "instance_ID" {
  value = aws_instance.ec2_polars.id
}
