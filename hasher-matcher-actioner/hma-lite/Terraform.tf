# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

provider "aws" {
  region = "us-east-1"
}

terraform {
    backend "s3" {
      bucket = "threatexchange-tf-state"
      key = "state/hasher-matcher-actioner-hmalite-dipanjanm.tfstate"
      region = "us-east-1"
      dynamodb_table = "terraform-state-locking"
    }
}

resource "aws_s3_bucket" "dist_bucket" {
  bucket = "dipanjanm-hmalite-beanstalk-dist"
  acl    = "private"
}

resource "aws_s3_bucket_object" "dist_item" {
  key    = "prod/dist-${uuid()}"
  bucket = aws_s3_bucket.dist_bucket.id
  source = "docker-compose.yml"
}

resource "aws_elastic_beanstalk_application" "hmalite" {
  name        = "hmalite"
  description = "Runs HMA Lite flask application."
}

resource "aws_elastic_beanstalk_application_version" "default" {
  name        = "hmalite-prod-${uuid()}"
  application = aws_elastic_beanstalk_application.hmalite.name
  description = "application version created by terraform"
  bucket      = aws_s3_bucket.dist_bucket.id
  key         = aws_s3_bucket_object.dist_item.id
}

data "aws_iam_policy_document" "instance-assume-role-policy" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["elasticbeanstalk.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "hmalite_bnstk_instance_role" {
  name_prefix = "hmalite_bnstk_instance_role-"
  assume_role_policy = data.aws_iam_policy_document.instance-assume-role-policy.json
  managed_policy_arns = ["arn:aws:iam::aws:policy/AWSElasticBeanstalkWebTier"]
}

resource "aws_iam_instance_profile" "hmalite_bnstk_instance_profile" {
  name_prefix = "hmalite_bnstk_instance_profile-"
  role = aws_iam_role.hmalite_bnstk_instance_role.name
}

resource "aws_iam_role" "hmalite_bnstk_service_role" {
  name_prefix = "hmalite_bnstk_service_role-"
  assume_role_policy = data.aws_iam_policy_document.instance-assume-role-policy.json
  managed_policy_arns = ["arn:aws:iam::aws:policy/service-role/AWSElasticBeanstalkEnhancedHealth"]
}

resource "aws_elastic_beanstalk_environment" "hmalite-prod" {
  name                = "hmalite-prod-2" # hmalite-prod began to fail to get assigned.
  application         = aws_elastic_beanstalk_application.hmalite.name
  solution_stack_name = "64bit Amazon Linux 2 v3.2.5 running Docker"

  setting {
    namespace = "aws:autoscaling:launchconfiguration"
    name = "IamInstanceProfile"
    value = aws_iam_instance_profile.hmalite_bnstk_instance_profile.arn
  }

  setting {
    namespace = "aws:elasticbeanstalk:environment"
    name      = "ServiceRole"
    value     = aws_iam_role.hmalite_bnstk_service_role.arn
  }

  setting {
    namespace ="aws:ec2:vpc"
    name      = "VPCId"
    value = "vpc-${vpcid}"
  }

  setting {
    namespace ="aws:ec2:vpc"
    name      = "Subnets"
    value = "subnet-${bunch-of-subnets}"
  }

  setting {
    namespace = "aws:ec2:vpc"
    name = "AssociatePublicIpAddress"
    value = "true"
  }
  setting {
    namespace = "aws:ec2:vpc"
    name = "ELBScheme"
    value = "internal"
  }
  setting {
    namespace = "aws:autoscaling:launchconfiguration"
    name = "InstanceType"
    value = "t2.nano"
  }
  setting {
    namespace = "aws:autoscaling:asg"
    name = "MinSize"
    value = "1"
  }
  setting {
    namespace = "aws:autoscaling:asg"
    name = "MaxSize"
    value = "1"
  }
  setting {
    namespace = "aws:elb:loadbalancer"
    name = "CrossZone"
    value = "true"
  }
}

output "app_version" {
  value = aws_elastic_beanstalk_application_version.default.name
}
