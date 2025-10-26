variable "region" {
    default = "us-east-1" 
}

variable "cluster_name" {
    default = "emr-cluster-ssm" 
}

variable "release_label" {
    default = "emr-7.10.0" 
}

variable "master_instance_type" {
    default = "m5.xlarge" 
}

variable "core_instance_type" {
    default = "m5.xlarge" 
}

variable "default_subnet_id"{
    default = "" 
}
