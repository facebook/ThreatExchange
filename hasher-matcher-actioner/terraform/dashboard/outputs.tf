# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

output "dashboard_name" {
  value = aws_cloudwatch_dashboard.basic_dashboard.dashboard_name
}
