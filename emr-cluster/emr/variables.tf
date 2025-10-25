variable "cluster_name" {
     type = string
}

variable "release_label" {
     type = string
}

variable "master_instance_type" {
     type = string
}

variable "core_instance_type" {
     type = string
}

variable "default_subnet_id" {
    type = string
    default = "" 
}
