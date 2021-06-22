# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

locals {

  queues_to_monitor_items = [for queue_name in var.queues_to_monitor : {
    width  = 6
    type   = "metric"
    period = 60
    properties = {
      title  = "${queue_name}: Age of Oldest Item"
      region = "${var.region}"
      stat   = "Maximum"
      metrics = [
        [
          "AWS/SQS", "ApproximateNumberOfMessagesVisible",
          "QueueName", "${queue_name}", { stat = "Average" }
        ],
        [".", "ApproximateAgeOfOldestMessage", ".", ".", { yAxis = "right" }]
      ]
    }
    }
  ]

  lambdas_to_monitor_widgets = [for function_name in var.lambdas_to_monitor : {
    width  = 6
    type   = "metric"
    period = 60
    properties = {
      title  = "${function_name} λ Invocations & Duration"
      region = "${var.region}"
      stat   = "Sum"
      metrics = [
        [
          "AWS/Lambda", "Invocations",
          "FunctionName", "${function_name}"
        ],
        [".", "Errors", ".", ".", { color = "#d62728" }],
        [".", "ConcurrentExecutions", ".", ".", { stat = "Maximum" }],
        [".", "Throttles", ".", ".", { label = "Throttles", color = "#ff9896" }],
        [".", "Duration", ".", ".", { stat = "p90", label = "p90", yAxis = "right" }],
        ["...", { label = "Av", stat = "Average", yAxis = "right", color = "#ff7f0e" }]
      ]
    }
    }
  ]
  total_concurrnet_lambda = {
    width  = 6
    type   = "metric"
    period = 60
    properties = {
      title   = "Total Concurrent  λ Executions"
      region  = "${var.region}"
      stacked = true
      stat    = "Maximum"
      metrics = [for function_name in var.lambdas_to_monitor : ["AWS/Lambda", "ConcurrentExecutions", "FunctionName", "${function_name}"]]
    }
  }
  api_gateway_widget = {
    width  = 6
    type   = "metric"
    period = 60
    properties = {
      title  = "API Gateway (${var.api_gateway_id})"
      region = "${var.region}"
      stat   = "Sum"
      metrics = [
        ["AWS/ApiGateway", "4xx", "Stage", "$default", "ApiId", "${var.api_gateway_id}"],
        [".", "5xx", ".", ".", ".", "."],
        [".", "Count", ".", ".", ".", "."],
        [".", "DataProcessed", ".", ".", ".", ".", { yAxis = "right" }]
      ]
    }
  }
  datastore_widgets_units = {
    width  = 6
    type   = "metric"
    period = 60
    properties = {
      title  = "DynamoDB R/W Units (WIP: Consult ${var.datastore.name} for actual numbers)",
      region = "${var.region}",
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
  }
  datastore_widgets_errors = {
    width  = 6
    type   = "metric"
    period = 60
    properties = {
      title  = "DynamoDB Errors, Throttles, & Conflicts",
      region = "${var.region}",
      stat   = "Sum",
      metrics = [
        ["AWS/DynamoDB", "ThrottledRequests", "TableName", "${var.datastore.name}", "Operation", "TransactWriteItems"],
        [".", "SystemErrors", ".", ".", ".", "."],
        [".", "ThrottledRequests", ".", ".", ".", "UpdateItem", { yAxis = "left" }],
        [".", "WriteThrottleEvents", ".", ".", "GlobalSecondaryIndexName", "GSI-2", { yAxis = "left" }],
        [".", "TransactionConflict", ".", ".", { yAxis = "right" }]
      ]
    }
  }

  dashboard_body = jsonencode({
    "widgets" = flatten([
      local.lambdas_to_monitor_widgets,
      local.queues_to_monitor_items,
      local.total_concurrnet_lambda,
      local.api_gateway_widget,
      local.datastore_widgets_units,
      local.datastore_widgets_errors
    ])
  })
}

resource "aws_cloudwatch_dashboard" "basic_dashboard" {
  dashboard_name = "${var.prefix}-dashboard"
  // tf converts numbers to strings when putting them in a list.
  // this strip quotes around numbers, so that {"value": "123"} turns into {"value": 123}
  dashboard_body = replace(local.dashboard_body, "/\"([0-9]+)\"/", "$1")
}
