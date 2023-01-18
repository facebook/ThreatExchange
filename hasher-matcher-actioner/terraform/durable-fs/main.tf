# Copyright (c) Meta Platforms, Inc. and affiliates.

data "aws_region" "current" {}

/*
 * # Durable file system
 * Hashing labmda uses an elastic file-system to write hashes at a
 * high-througput. The files so-generated are used in other lambdas to create
 * clusters from recently seen content.
 *
 * EFS can only be mounted onto lambdas that are connected to a VPC. So, this
 * module ends up creating a dedicated VPC.
 */
resource "aws_efs_file_system" "lcc_durable_fs" {
  creation_token = "${var.prefix}-lcc-durable-filesystem"

  tags = merge(
    var.additional_tags,
    {
      Name = "LCC_DurableFS"
    }
  )
}

# Create a VPC for EFS mounts
module "lcc_efs_vpc" {
  source = "terraform-aws-modules/vpc/aws"

  name          = "${var.prefix}-lcc-efs-vpc"
  cidr          = "10.10.0.0/16"
  azs           = ["${data.aws_region.current.name}a", "${data.aws_region.current.name}b", "${data.aws_region.current.name}c"]
  intra_subnets = ["10.10.101.0/24"]
}

# Mount target connects the file system to the subnet
resource "aws_efs_mount_target" "lcc_durable_fs" {
  file_system_id  = aws_efs_file_system.lcc_durable_fs.id
  subnet_id       = module.lcc_efs_vpc.intra_subnets[0]
  security_groups = [module.lcc_efs_vpc.default_security_group_id]
}

# EFS access point used by lambda file system
resource "aws_efs_access_point" "access_point_for_lambda" {
  file_system_id = aws_efs_file_system.lcc_durable_fs.id

  root_directory {
    path = "/lambda"
    creation_info {
      owner_gid   = 1000
      owner_uid   = 1000
      permissions = "777"
    }
  }

  posix_user {
    gid = 1000
    uid = 1000
  }
}
