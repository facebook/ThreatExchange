# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

output "image_notification_topic_arn" {
  value = aws_sns_topic.image_notification_topic.arn
}

output "data_bucket_arn" {
  value = aws_s3_bucket.data_bucket.arn
}

output "image_folder_key" {
  value = aws_s3_bucket_object.images.id
}
