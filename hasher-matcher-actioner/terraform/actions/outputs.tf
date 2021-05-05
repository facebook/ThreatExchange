# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

output "writebacks_queue" {
  value = {
    url = aws_sqs_queue.writebacks_queue.id,
    arn = aws_sqs_queue.writebacks_queue.arn
  }
}
