variable "region" {
  default = "us-east-1"
}

variable "instance_type" {
  default = "t3.micro"
}

variable "user_data" {
    description = "Startup script to execute when creating an instance"
}