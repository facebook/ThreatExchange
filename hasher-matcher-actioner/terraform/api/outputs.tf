# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

output "invoke_url" {
  value = aws_apigatewayv2_stage.hma_apigateway.invoke_url
}
