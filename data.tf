// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

data "aws_ami" "default" {
  most_recent = true
  owners      = [var.msk_ami_account_id]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-2.*-x86_64-gp2"]
  }
}

data "aws_msk_broker_nodes" "example" {
  cluster_arn = aws_msk_cluster.example.arn
}

data "aws_availability_zones" "available" {}