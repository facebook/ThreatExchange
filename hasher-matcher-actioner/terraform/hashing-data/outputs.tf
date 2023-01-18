# Copyright (c) Meta Platforms, Inc. and affiliates.

output "image_folder_info" {
  value = {
    bucket_name        = var.data_bucket.bucket_name
    key                = aws_s3_bucket_object.images.id
    notification_topic = aws_sns_topic.image_notification_topic.arn
  }
}

output "threat_exchange_data_folder_info" {
  value = {
    bucket_name        = var.data_bucket.bucket_name
    key                = aws_s3_bucket_object.threat_exchange_data.id
    notification_topic = aws_sns_topic.threat_exchange_data.arn
  }
}

output "index_folder_info" {
  value = {
    bucket_name = var.data_bucket.bucket_name
    key         = aws_s3_bucket_object.index.id
  }
}
