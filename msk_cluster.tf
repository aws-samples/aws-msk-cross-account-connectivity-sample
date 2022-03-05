// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

resource "aws_security_group" "msk_cluster" {
  vpc_id = module.vpc_msk.vpc_id
}

resource "aws_security_group_rule" "msk_cluster_ingress_all" {
  type              = "ingress"
  from_port         = 0
  to_port           = 65535
  protocol          = "tcp"
  cidr_blocks       = ["10.0.0.0/8"]
  security_group_id = aws_security_group.msk_cluster.id
}

resource "aws_msk_cluster" "example" {
  cluster_name           = "example"
  kafka_version          = var.msk_kafka_version
  number_of_broker_nodes = var.num_brokers

  broker_node_group_info {
    instance_type   = var.msk_instance_type
    ebs_volume_size = var.msk_ebs_volume_size
    client_subnets  = module.vpc_msk.public_subnets
    security_groups = [aws_security_group.msk_cluster.id]
  }
}
resource "aws_ssm_parameter" "clusterlist" {
  name  = "/msk/cluster/list"
  type  = "String"
  value = jsonencode(local.cluster_list_ssm_format)
  depends_on = [
    aws_msk_cluster.example,
  ]
}

resource "aws_ssm_parameter" "configlist" {
  name  = "/msk/cluster/node/config/list"
  type  = "String"
  value = "{}"
  lifecycle {
    ignore_changes = [value] # the value will be managed by the Kafka script
  }
}

resource "aws_ssm_parameter" "runtime_settings" {
  name      = "/msk/cluster/node/settings"
  type      = "String"
  value     = local.runtime_settings
  overwrite = true
}