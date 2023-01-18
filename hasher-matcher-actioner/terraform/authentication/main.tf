# Copyright (c) Meta Platforms, Inc. and affiliates.

# The three resource configurations below were directly copied to
# /authentication-shared/main.tf and adjusted so that their names were
# unique (to keep terraform state from getting confused). Consider
# /authentication-shared/main.tf when making changes here.

resource "aws_cognito_user_pool" "webapp_and_api_user_pool" {
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
  count                    = var.use_shared_user_pool ? 0 : 1
  auto_verified_attributes = ["email"]
  name                     = "${var.prefix}-hma-user-pool"
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

resource "aws_cognito_user_pool_domain" "webapp_user_pool_domain" {
  count        = var.use_shared_user_pool ? 0 : 1
  domain       = "${var.organization}-${var.prefix}-hma-webapp"
  user_pool_id = aws_cognito_user_pool.webapp_and_api_user_pool[0].id
}

resource "aws_cognito_user_pool_client" "webapp_and_api_user_pool_client" {
  count                                = var.use_shared_user_pool ? 0 : 1
  name                                 = "${var.prefix}-hma-user-pool-client"
  user_pool_id                         = aws_cognito_user_pool.webapp_and_api_user_pool[0].id
  generate_secret                      = false
  allowed_oauth_flows_user_pool_client = true
  explicit_auth_flows                  = ["ALLOW_ADMIN_USER_PASSWORD_AUTH", "ALLOW_USER_SRP_AUTH", "ALLOW_REFRESH_TOKEN_AUTH"]
  allowed_oauth_scopes                 = ["openid"]
  allowed_oauth_flows                  = ["code"]
  callback_urls                        = var.use_cloudfront_distribution_url ? [var.cloudfront_distribution_url] : ["https://localhost:3000"]
  logout_urls                          = var.use_cloudfront_distribution_url ? [var.cloudfront_distribution_url] : ["https://localhost:3000"]
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
