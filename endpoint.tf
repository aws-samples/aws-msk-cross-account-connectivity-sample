// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

resource "aws_vpc_endpoint_service" "msk" {
  acceptance_required        = false
  network_load_balancer_arns = [aws_lb.msk.arn]
}

resource "aws_security_group" "msk_endpoint" {
  vpc_id = module.vpc_client.vpc_id
}

resource "aws_security_group_rule" "msk_endpoint_ingress_all" {
  type              = "ingress"
  from_port         = 0
  to_port           = 65535
  protocol          = "tcp"
  cidr_blocks       = [module.vpc_client.vpc_cidr_block]
  security_group_id = aws_security_group.msk_endpoint.id
}

resource "aws_vpc_endpoint" "msk" {
  vpc_id             = module.vpc_client.vpc_id
  service_name       = aws_vpc_endpoint_service.msk.service_name
  vpc_endpoint_type  = "Interface"
  security_group_ids = [aws_security_group.msk_endpoint.id]
}

resource "aws_vpc_endpoint_subnet_association" "msk" {
  vpc_endpoint_id = aws_vpc_endpoint.msk.id
  subnet_id       = module.vpc_client.public_subnets[0]
}