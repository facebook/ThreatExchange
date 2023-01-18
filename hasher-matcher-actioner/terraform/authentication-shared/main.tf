# Copyright (c) Meta Platforms, Inc. and affiliates.

# This terraform configuration script is used in isolation to configure
# a shared shared user pool to be used across a team of developers /
# engineers that are collaborating on HMA developemnt within a single
# AWS account.

# The three resource configurations below were directly copied from
# /authentication/main.tf and adjusted so that their names were
# unique (to keep terraform state from getting confused). Consider
# /authentication/main.tf when making changes here.

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_cognito_user_pool" "webapp_and_api_shared_user_pool" {
  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
    recovery_mechanism {
      name     = "verified_phone_number"
      priority = 2
    }
  }
  admin_create_user_config {
    allow_admin_create_user_only = true
  }
  auto_verified_attributes = ["email"]
  name                     = "shared-hma-user-pool"
  password_policy {
    minimum_length                   = 8
    require_lowercase                = true
    require_numbers                  = true
    require_symbols                  = true
    require_uppercase                = true
    temporary_password_validity_days = 1
  }
  schema {
    name                = "email"
    attribute_data_type = "String"
    mutable             = true
    required            = true
    string_attribute_constraints {
      min_length = 5
      max_length = 254
    }
  }
  username_configuration {
    case_sensitive = false
  }
}

resource "aws_cognito_user_pool_domain" "webapp_shared_user_pool_domain" {
  domain       = "${var.organization}-shared-hma-webapp"
  user_pool_id = aws_cognito_user_pool.webapp_and_api_shared_user_pool.id
}

resource "aws_cognito_user_pool_client" "webapp_and_api_shared_user_pool_client" {
  name                                 = "shared-hma-user-pool-client"
  user_pool_id                         = aws_cognito_user_pool.webapp_and_api_shared_user_pool.id
  generate_secret                      = false
  allowed_oauth_flows_user_pool_client = true
  explicit_auth_flows                  = ["ALLOW_ADMIN_USER_PASSWORD_AUTH", "ALLOW_USER_SRP_AUTH", "ALLOW_REFRESH_TOKEN_AUTH"]
  allowed_oauth_scopes                 = ["openid"]
  allowed_oauth_flows                  = ["code"]
  callback_urls                        = ["https://localhost:3000"] # a shared user pool and its app client is for developers only
  logout_urls                          = ["https://localhost:3000"] # a shared user pool and its app client is for developers only
  supported_identity_providers         = ["COGNITO"]
  prevent_user_existence_errors        = "ENABLED"
  token_validity_units {
    access_token  = "minutes"
    id_token      = "minutes"
    refresh_token = "days"
  }
  refresh_token_validity = 30
  access_token_validity  = 60
  id_token_validity      = 60
}
