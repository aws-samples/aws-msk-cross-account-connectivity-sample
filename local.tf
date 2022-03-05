// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

locals {
  azs          = data.aws_availability_zones.available.names
  cluster_list = [data.aws_msk_broker_nodes.example]
  cluster_list_ssm_format = {
    for k in local.cluster_list :
    k.cluster_arn => k.node_info_list[*]
  }
  runtime_settings = jsonencode({
    binaries_s3_bucket         = var.binaries_s3_bucket
    log_s3_bucket              = var.binaries_s3_bucket
    confluent_package_filename = var.confluent_package_filename
    java_version_name          = "java-1.8.0-openjdk"
    s3_endpoint_type           = "gateway"
    kafka_properties           = { "security.protocol" = "SSL" }
  })

  example_nodeinfolist = data.aws_msk_broker_nodes.example.node_info_list

}
