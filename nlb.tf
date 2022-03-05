// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

resource "aws_lb" "msk" {
  name               = "msk"
  load_balancer_type = "network"
  internal           = true

  subnet_mapping {
    subnet_id = module.vpc_msk.public_subnets[0]
  }

  subnet_mapping {
    subnet_id = module.vpc_msk.public_subnets[1]
  }

  subnet_mapping {
    subnet_id = module.vpc_msk.public_subnets[2]
  }
}

resource "aws_lb_target_group" "nlb_target_groups" {
  #count    = length(local.example_nodeinfolist)
  count       = var.num_brokers
  name        = "dyanmic-broker${count.index}"
  port        = 9094
  protocol    = "TCP"
  target_type = "ip"
  vpc_id      = module.vpc_msk.vpc_id
}

resource "aws_lb_target_group_attachment" "tgr_attachment" {
  for_each = {
    for i, k in aws_lb_target_group.nlb_target_groups :
    i => {
      target_group = aws_lb_target_group.nlb_target_groups[i]
      instance_ip  = data.aws_msk_broker_nodes.example.node_info_list[i].client_vpc_ip_address
      broker_id    = data.aws_msk_broker_nodes.example.node_info_list[i].broker_id
    }
  }
  target_group_arn = each.value.target_group.arn
  target_id        = each.value.instance_ip
  #port             = 9000+each.value.broker_id
}

resource "aws_lb_listener" "nlb_listerner" {
  for_each = {
    for i, k in aws_lb_target_group.nlb_target_groups :
    i => {
      target_group = aws_lb_target_group.nlb_target_groups[i]
      broker_id    = data.aws_msk_broker_nodes.example.node_info_list[i].broker_id
    }
  }
  load_balancer_arn = aws_lb.msk.arn
  port              = 9000 + each.value.broker_id
  protocol          = "TCP"

  default_action {
    type             = "forward"
    target_group_arn = each.value.target_group.arn
  }
}

resource "aws_lb_target_group" "all_brokers" {
  name        = "allbrokers"
  port        = 9094
  protocol    = "TCP"
  target_type = "ip"
  vpc_id      = module.vpc_msk.vpc_id
}

resource "aws_lb_target_group_attachment" "all_brokers_broker" {
  count            = var.num_brokers
  target_group_arn = aws_lb_target_group.all_brokers.arn
  target_id        = data.aws_msk_broker_nodes.example.node_info_list[count.index].client_vpc_ip_address
}

resource "aws_lb_listener" "all_brokers" {
  load_balancer_arn = aws_lb.msk.arn
  port              = "9094"
  protocol          = "TCP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.all_brokers.arn
  }
}
