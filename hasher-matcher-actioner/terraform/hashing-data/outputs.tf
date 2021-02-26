# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

output "image_folder_info" {
  value = {
    bucket_name        = aws_s3_bucket.data_bucket.id
    key                = aws_s3_bucket_object.images.id
    notification_topic = aws_sns_topic.image_notification_topic.arn
  }
}

output "threat_exchange_data_folder_info" {
  value = {
    bucket_name        = aws_s3_bucket.data_bucket.id
    key                = aws_s3_bucket_object.threat_exchange_data.id
    notification_topic = aws_sns_topic.threat_exchange_data.arn
  }
}

output "index_folder_info" {
  value = {
    bucket_name = aws_s3_bucket.data_bucket.id
    key         = aws_s3_bucket_object.index.id
  }
}

output "hma_datastore" {
  value = {
    name = aws_dynamodb_table.datastore.id
    arn  = aws_dynamodb_table.datastore.arn
  }
}
