# Copyright (c) Meta Platforms, Inc. and affiliates.

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

data "aws_region" "default" {}

locals {
  common_tags = merge(var.additional_tags, {
    "HMAPrefix"  = var.prefix
    "VPCExample" = "vpc-eg"
  })
  region = data.aws_region.default.name
}

### VPC (eg) ###
module "vpc_eg" {
  source = "terraform-aws-modules/vpc/aws"

  name            = "${var.prefix}-eg-vpc"
  cidr            = "20.10.0.0/16"
  azs             = ["${local.region}a", "${local.region}b", "${local.region}c"]
  private_subnets = ["20.10.1.0/24", "20.10.2.0/24", "20.10.3.0/24"]
  public_subnets  = ["20.10.11.0/24", "20.10.12.0/24", "20.10.13.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = true

  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(var.additional_tags, {
    Terraform   = "true"
    Environment = "dev"
  })
}


# VPN https://docs.aws.amazon.com/vpn/latest/clientvpn-admin/cvpn-getting-started.html
# after following https://docs.aws.amazon.com/vpn/latest/clientvpn-admin/client-authentication.html#mutual

data "aws_acm_certificate" "client" {
  domain   = "client1.domain.tld"
  statuses = ["ISSUED"]
}

data "aws_acm_certificate" "server" {
  domain   = "server"
  statuses = ["ISSUED"]
}

resource "aws_ec2_client_vpn_endpoint" "eg" {
  server_certificate_arn = data.aws_acm_certificate.server.arn
  client_cidr_block      = "10.0.0.0/16"

  authentication_options {
    type                       = "certificate-authentication"
    root_certificate_chain_arn = data.aws_acm_certificate.client.arn
  }

  connection_log_options {
    enabled = false
  }
}

resource "aws_ec2_client_vpn_network_association" "eg" {
  depends_on = [
    module.vpc_eg.public_subnets
  ]
  client_vpn_endpoint_id = aws_ec2_client_vpn_endpoint.eg.id
  subnet_id              = module.vpc_eg.public_subnets[0]
}

resource "aws_ec2_client_vpn_authorization_rule" "eg" {
  client_vpn_endpoint_id = aws_ec2_client_vpn_endpoint.eg.id
  target_network_cidr    = module.vpc_eg.vpc_cidr_block
  authorize_all_groups   = true
}

resource "aws_ec2_client_vpn_route" "eg" {
  client_vpn_endpoint_id = aws_ec2_client_vpn_endpoint.eg.id
  destination_cidr_block = "0.0.0.0/0"
  target_vpc_subnet_id   = aws_ec2_client_vpn_network_association.eg.subnet_id
}
