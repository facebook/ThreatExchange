# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

output "image_notification_topic_arn" {
  value = aws_sns_topic.image_notification_topic.arn
}
