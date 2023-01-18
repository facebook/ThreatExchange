# Copyright (c) Meta Platforms, Inc. and affiliates.

output "vpc_id" {
  value = module.vpc_eg.vpc_id
}
output "pub_subnets" {
  value = module.vpc_eg.public_subnets
}
output "priv_subnets" {
  value = module.vpc_eg.private_subnets
}
output "security_group_id" {
  value = module.vpc_eg.default_security_group_id
}
output "vpc_cidr_block" {
  value = module.vpc_eg.vpc_cidr_block
}
