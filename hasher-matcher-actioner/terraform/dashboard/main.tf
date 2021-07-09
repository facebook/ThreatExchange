# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

locals {
  title_glance = jsonencode({
    height = 1,
    width  = 24,
    type   = "text",
    properties = {
      markdown = "## Hashing, Matching &amp; Actioning at a Glance"
    }
  })

  title_dynamodb = jsonencode({
    height = 1,
    width  = 24,
    type   = "text",
    properties = {
      markdown = "# DynamoDB"
    }
  })

  title_api = jsonencode({
    height = 1,
    width  = 24,
    type   = "text",
    properties = {
      markdown = "# API"
    }
  })

  title_system_capacity = jsonencode({
    height = 1,
    width  = 24,
    type   = "text",
    properties = {
      markdown = "# System Capacity"
    }
  })

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
    width = 12
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

  api_lambda_widget = jsonencode({
    height = 6,
    width  = 12,
    type   = "metric",
    properties = {
      metrics = [
        ["AWS/Lambda", "Invocations", "FunctionName", "${var.api_lambda_name}", { label = "Requests" }],
        [".", "Errors", ".", ".", { color = "#d62728", yAxis = "left" }],
        [".", "ConcurrentExecutions", ".", ".", { stat = "Maximum", yAxis = "right" }],
        [".", "Throttles", ".", ".", { color = "#ff9896", label = "Throttles" }]
      ],
      period  = 60,
      region  = "${var.region}",
      stat    = "Sum",
      title   = "API Requests & λ Concurrency ",
      view    = "timeSeries",
      stacked = false
    }
  })

  api_response_times = jsonencode({
    height = 6,
    width  = 6,
    type   = "metric",
    properties = {
      metrics = [
        ["AWS/Lambda", "Duration", "FunctionName", "${var.api_lambda_name}", { label = "p90", stat = "p90", yAxis = "right" }],
        ["...", { color = "#ff7f0e", label = "Av", stat = "Average", yAxis = "right" }]
      ],
      period  = 60,
      region  = "${var.region}",
      stat    = "Sum",
      title   = "API Response Times (p90 and avg)",
      view    = "timeSeries",
      stacked = false
    }
  })

  api_gateway_widget = jsonencode({
    width = 6
    type  = "metric"
    properties = {
      metrics = [
        [{ expression = "100*(m1/m3)", label = "4xx %age", id = "e1", color = "#ff7f0e", yAxis = "right" }],
        [{ expression = "100*(m2/m3)", label = "5xx %age", id = "e2", color = "#d62728", yAxis = "right" }],
        ["AWS/ApiGateway", "4xx", "Stage", "$default", "ApiId", "mc620fy2hf", { id = "m1", visible = false }],
        [".", "5xx", ".", ".", ".", ".", { color = "#d62728", id = "m2", visible = false }],
        [".", "Count", ".", ".", ".", ".", { id = "m3", label = "Requests" }]
      ],
      period  = 60,
      region  = "${var.region}"
      stat    = "Sum",
      title   = "API Request Volume and %age 4xx, 5xx",
      view    = "timeSeries",
      stacked = false,
      yAxis = {
        right = {
          min = 0,
          max = 100
        }
      }
    }
  })

  dynamodb_datastore_rwcu_widget = jsonencode({
    width  = 8
    type   = "metric"
    period = 60
    properties = {
      title  = "Read/Write Capacity Units Utilized",
      region = "${var.region}",
      period = 60
      stat   = "Sum",
      metrics = [
        ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", "${var.datastore.name}", { yAxis = "left", label = "Primary RCUs" }],
        [".", "ConsumedWriteCapacityUnits", ".", ".", { label = "Primary WCUs", color = "#aec7e8" }],
        [".", "ConsumedReadCapacityUnits", ".", ".", "GlobalSecondaryIndexName", "GSI-2", { yAxis = "left", label = "GSI-2 RCUs" }],
        [".", "ConsumedWriteCapacityUnits", ".", ".", ".", ".", { label = "GSI-2 WCUs", color = "#98df8a" }],
        [".", "ConsumedReadCapacityUnits", ".", ".", ".", "GSI-1", { yAxis = "left", label = "GSI-1 RCUs" }],
        [".", "ConsumedWriteCapacityUnits", ".", ".", ".", ".", { label = "GSI-1 WCUs", color = "#c5b0d5" }]
      ]
    }
  })

  dynamodb_datastore_errors_widget = jsonencode({
    width = 8
    type  = "metric"
    properties = {
      title  = "Errors, Throttles &amp; Conflicts",
      region = "${var.region}",
      period = 60
      stat   = "Sum",
      metrics = [
        ["AWS/DynamoDB", "ThrottledRequests", "TableName", "${var.datastore.name}", "Operation", "PutItem", { label = "Throttled Puts" }],
        ["...", "UpdateItem", { label = "Throttled Updates", color = "#17becf" }],
        ["...", "TransactWriteItems", { label = "Throttled Batch Writes", color = "#bcbd22" }],
        [".", "TransactionConflict", ".", ".", { yAxis = "right" }],
      [".", "WriteThrottleEvents", ".", ".", { yAxis = "right" }]]
    }
  })

  dashboard_body = <<JSON
  {
    "widgets": [
      ${local.title_glance},
      ${join(", ", local.pipeline_lambdas_widgets)},
      ${join(", ", local.queues_to_monitor_items)},

      ${local.title_api},
      ${local.api_lambda_widget},
      ${local.api_response_times},
      ${local.api_gateway_widget},

      ${local.title_dynamodb},
      ${local.dynamodb_datastore_rwcu_widget},
      ${local.dynamodb_datastore_errors_widget},

      ${local.title_system_capacity},
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
