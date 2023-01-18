# Copyright (c) Meta Platforms, Inc. and affiliates.

output "primary_datastore" {
  # To any module requiring both name and arn, you can pass in this shape
  # directly.

  value = {
    name       = aws_dynamodb_table.hma_datastore.name
    arn        = aws_dynamodb_table.hma_datastore.arn
    stream_arn = aws_dynamodb_table.hma_datastore.stream_arn
  }
}

output "banks_datastore" {
  value = {
    name       = aws_dynamodb_table.hma_banks.name
    arn        = aws_dynamodb_table.hma_banks.arn
    stream_arn = aws_dynamodb_table.hma_banks.stream_arn
  }
}


output "counts_datastore" {
  value = {
    name = aws_dynamodb_table.hma_counts.name
    arn  = aws_dynamodb_table.hma_counts.arn
  }
}
