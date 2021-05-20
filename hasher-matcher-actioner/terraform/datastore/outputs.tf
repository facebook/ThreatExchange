# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

output "primary_datastore" {
    # To any module requiring both name and arn, you can pass in this shape
    # directly.

    value = {
        name = aws_dynamodb_table.hma_datastore.name
        arn  = aws_dynamodb_table.hma_datastore.arn
    }
}