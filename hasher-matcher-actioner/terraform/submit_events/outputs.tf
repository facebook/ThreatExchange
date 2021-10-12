# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

output "submit_topic_arn" {
  value = aws_sns_topic.submit_event_notification_topic.arn
}
