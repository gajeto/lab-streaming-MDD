output "cluster_id" {
  value = module.cluster.cluster_id
}

output "master_node_instance_id" {
  value       = try(local.master_ids[0], null)
}