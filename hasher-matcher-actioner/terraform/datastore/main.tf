# Copyright (c) Meta Platforms, Inc. and affiliates.

# Global Secondary Index definitions need to change in tandem with
# hmalib/tests/test_pipeline_models.py::DATASTORE_TABLE_DEF

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

  stream_enabled   = true
  stream_view_type = "NEW_IMAGE"

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
      "Labels",
      "SignalType",
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
      "Labels",
      "SignalType",
    ]
  }

  tags = merge(
    var.additional_tags,
    {
      Name = "HMADataStore"
    }
  )

  lifecycle {
    # To prevent execution of plans which would cause this datastore to get
    # destroyed. Once in the hands of partners, we have to be extra careful to
    # not accidentally delete their data. 
    prevent_destroy = true
  }
}


### Bank Data Management Store
resource "aws_dynamodb_table" "hma_banks" {
  name         = "${var.prefix}-HMABanks"
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
    name = "BankNameIndex-BankName"
    type = "S"
  }

  attribute {
    name = "BankNameIndex-BankId"
    type = "S"
  }

  attribute {
    name = "BankMemberSignalCursorIndex-SignalType"
    type = "S"
  }

  attribute {
    name = "BankMemberSignalCursorIndex-ChronoKey"
    type = "S"
  }

  attribute {
    name = "BankMemberIdIndex-BankMemberId"
    type = "S"
  }

  stream_enabled   = true
  stream_view_type = "NEW_IMAGE"


  tags = merge(
    var.additional_tags,
    {
      Name = "HMABanks"
    }
  )

  lifecycle {
    # To prevent execution of plans which would cause this datastore to get
    # destroyed. Once in the hands of partners, we have to be extra careful to
    # not accidentally delete their data. 
    prevent_destroy = true
  }

  global_secondary_index {
    name            = "BankNameIndex"
    hash_key        = "BankNameIndex-BankName"
    range_key       = "BankNameIndex-BankId"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "BankMemberSignalCursorIndex"
    hash_key        = "BankMemberSignalCursorIndex-SignalType"
    range_key       = "BankMemberSignalCursorIndex-ChronoKey"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "BankMemberIdIndex"
    hash_key        = "BankMemberIdIndex-BankMemberId"
    projection_type = "KEYS_ONLY"
  }
}


resource "aws_dynamodb_table" "hma_counts" {
  name         = "${var.prefix}-HMACounts"
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
}
