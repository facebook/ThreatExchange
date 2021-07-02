# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

### Primary hashing / matching / actions datastore 
resource "aws_dynamodb_table" "hma_datastore" {
  name         = "${var.prefix}-HMADataStore"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "PK"
  range_key    = "SK"
  attribute {
    name = "PK"
    type = "S"
  }
  attribute {
    name = "SK"
    type = "S"
  }
  attribute {
    name = "GSI1-PK"
    type = "S"
  }
  attribute {
    name = "GSI1-SK"
    type = "S"
  }
  attribute {
    name = "GSI2-PK"
    type = "S"
  }
  attribute {
    name = "UpdatedAt"
    type = "S"
  }

  global_secondary_index {
    name            = "GSI-1"
    hash_key        = "GSI1-PK"
    range_key       = "GSI1-SK"
    projection_type = "INCLUDE"
    non_key_attributes = [
      "ContentHash",
      "UpdatedAt",
      "SignalHash",
      "SignalSource",
      "HashType",
      "Labels"
    ]
  }

  global_secondary_index {
    name            = "GSI-2"
    hash_key        = "GSI2-PK"
    range_key       = "UpdatedAt"
    projection_type = "INCLUDE"
    non_key_attributes = [
      "ContentHash",
      "SignalHash",
      "SignalSource",
      "HashType",
      "Labels"
    ]
  }

  tags = merge(
    var.additional_tags,
    {
      Name = "HMADataStore"
    }
  )
}
