# Copyright (c) Meta Platforms, Inc. and affiliates.

output "durable_fs_security_group_ids" {
  value = [module.lcc_efs_vpc.default_security_group_id]
}

output "durable_fs_subnet_ids" {
  value = module.lcc_efs_vpc.intra_subnets
}

output "durable_fs_arn" {
  value = aws_efs_access_point.access_point_for_lambda.arn
}
