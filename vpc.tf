// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

###############################################################################
# MSK VPC
###############################################################################

module "vpc_msk" {
  source = "terraform-aws-modules/vpc/aws"

  name                 = "msk"
  cidr                 = "10.0.0.0/16"
  enable_dns_hostnames = true

  azs            = local.azs
  public_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

###############################################################################
# Client VPC
###############################################################################

module "vpc_client" {
  source = "terraform-aws-modules/vpc/aws"

  name                 = "client"
  cidr                 = "10.0.0.0/16"
  enable_dns_hostnames = true

  azs            = [local.azs[0]]
  public_subnets = ["10.0.1.0/24"]
}