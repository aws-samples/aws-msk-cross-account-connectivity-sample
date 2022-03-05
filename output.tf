output "node_list" {
  value = aws_msk_cluster.example.bootstrap_brokers_tls
}

output "example_node_info_list" {
  value = data.aws_msk_broker_nodes.example
}