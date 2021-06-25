# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

locals {

  pipeline_lambdas_widgets = [for lambda in var.pipeline_lambdas : templatefile(
    "${path.module}/lambda_widget.tpl", {
      region = var.region, lambda_name = lambda[1], lambda_title = lambda[0]
    }
  )]

  queues_to_monitor_items = [for queue in var.queues_to_monitor : jsonencode({
    width = 6
    type  = "metric"
    properties = {
      title  = "${queue[0]}: Age of Oldest Item"
      region = "${var.region}"
      period = 60
      stat   = "Maximum"
      metrics = [
        [
          "AWS/SQS", "ApproximateNumberOfMessagesVisible",
          "QueueName", "${queue[1]}", { stat = "Average" }
        ],
        [".", "ApproximateAgeOfOldestMessage", ".", ".", { yAxis = "right" }]
      ]
    }
    })
  ]

  all_lambda_names = flatten([
    [for lambda in var.pipeline_lambdas : lambda[1]], [var.api_lambda_name], var.other_lambdas
  ])

  total_concurrent_lambda = jsonencode({
    width = 6
    type  = "metric"
    properties = {
      title   = "Total Concurrent λ Executions"
      region  = "${var.region}"
      stacked = true
      stat    = "Maximum"
      period  = 60
      metrics = [for lambda in local.all_lambda_names : ["AWS/Lambda", "ConcurrentExecutions", "FunctionName", "${lambda}"]]
    }
  })

  api_lambda_widget = templatefile("${path.module}/lambda_widget.tpl", { region = var.region, lambda_name = var.api_lambda_name, lambda_title = "API" })

  api_gateway_widget = jsonencode({
    width = 6
    type  = "metric"
    properties = {
      title  = "API Gateway (${var.api_gateway_id})"
      region = "${var.region}"
      period = 60
      stat   = "Sum"
      metrics = [
        ["AWS/ApiGateway", "4xx", "Stage", "$default", "ApiId", "${var.api_gateway_id}"],
        [".", "5xx", ".", ".", ".", "."],
        [".", "Count", ".", ".", ".", "."],
        [".", "DataProcessed", ".", ".", ".", ".", { yAxis = "right" }]
      ]
    }
  })

  datastore_widgets_units = jsonencode({
    width  = 6
    type   = "metric"
    period = 60
    properties = {
      title  = "DynamoDB R/W Units (WIP: Consult ${var.datastore.name} for actual numbers)",
      region = "${var.region}",
      period = 60
      stat   = "Average",
      metrics = [
        ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", "${var.datastore.name}", { yAxis = "right" }],
        [".", "ConsumedWriteCapacityUnits", ".", "."],
        [".", "ConsumedReadCapacityUnits", ".", ".", "GlobalSecondaryIndexName", "GSI-2", { yAxis = "right" }],
        [".", "ConsumedWriteCapacityUnits", ".", ".", ".", "."],
        [".", "ConsumedReadCapacityUnits", ".", ".", ".", "GSI-1", { yAxis = "right" }],
        [".", "ConsumedWriteCapacityUnits", ".", ".", ".", "."]
      ]
    }
  })

  datastore_widgets_errors = jsonencode({
    width = 6
    type  = "metric"
    properties = {
      title  = "DynamoDB Errors, Throttles, & Conflicts",
      region = "${var.region}",
      period = 60
      stat   = "Sum",
      metrics = [
        ["AWS/DynamoDB", "ThrottledRequests", "TableName", "${var.datastore.name}", "Operation", "TransactWriteItems"],
        [".", "SystemErrors", ".", ".", ".", "."],
        [".", "ThrottledRequests", ".", ".", ".", "UpdateItem", { yAxis = "left" }],
        [".", "WriteThrottleEvents", ".", ".", "GlobalSecondaryIndexName", "GSI-2", { yAxis = "left" }],
        [".", "TransactionConflict", ".", ".", { yAxis = "right" }]
      ]
    }
  })

  dashboard_body = <<JSON
  {
    "widgets": [
      ${join(", ", local.pipeline_lambdas_widgets)},
      ${join(", ", local.queues_to_monitor_items)},
      ${local.api_lambda_widget},
      ${local.api_gateway_widget},
      ${local.datastore_widgets_units},
      ${local.datastore_widgets_errors},
      ${local.total_concurrent_lambda}
      ]
  }
JSON
}

resource "aws_cloudwatch_dashboard" "basic_dashboard" {
  dashboard_name = var.name
  // tf converts numbers to strings when putting them in a list.
  // this strip quotes around numbers, so that {"value": "123"} turns into {"value": 123}
  dashboard_body = replace(local.dashboard_body, "/\"([0-9]+)\"/", "$1")
}
