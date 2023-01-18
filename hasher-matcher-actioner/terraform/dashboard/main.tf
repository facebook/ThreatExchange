# Copyright (c) Meta Platforms, Inc. and affiliates.

data "aws_region" "current" {}

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

  title_submit_event = jsonencode({
    height = 1,
    width  = 24,
    type   = "text",
    properties = {
      markdown = "# Submit Events (Submissions over SNS)"
    }
  })

  pipeline_lambdas_widgets = [for lambda in var.pipeline_lambdas : templatefile(
    "${path.module}/lambda_widget.tpl", {
      region = data.aws_region.current.name, lambda_name = lambda[1], lambda_title = lambda[0]
    }
  )]

  queues_to_monitor_items = [for queue in var.queues_to_monitor : jsonencode({
    width = 6
    type  = "metric"
    properties = {
      title  = "${queue[0]}: Age of Oldest Item"
      region = "${data.aws_region.current.name}"
      period = 60
      stat   = "Maximum"
      metrics = [
        [
          "AWS/SQS", "ApproximateNumberOfMessagesVisible",
          "QueueName", "${queue[1]}", { stat = "Average" }
        ],
        [".", "ApproximateAgeOfOldestMessage", ".", ".", { yAxis = "right" }],
        [
          "AWS/SQS", "ApproximateNumberOfMessagesVisible",
          "QueueName", "${queue[2]}", { stat = "Average", label = "dlq-approx-count" }
        ],
        [".", "ApproximateAgeOfOldestMessage", ".", ".", { yAxis = "right", label = "dlq-approx-age" }]
      ]
    }
    })
  ]

  all_lambda_names = flatten([
    [for lambda in var.pipeline_lambdas : lambda[1]], var.other_lambdas
  ])

  total_concurrent_lambda = jsonencode({
    width = 12
    type  = "metric"
    properties = {
      title   = "Total Concurrent λ Executions"
      region  = "${data.aws_region.current.name}"
      stacked = true
      stat    = "Maximum"
      period  = 60
      metrics = [for lambda in local.all_lambda_names : ["AWS/Lambda", "ConcurrentExecutions", "FunctionName", "${lambda}"]]
    }
  })

  api_lambda_widget = jsonencode({
    height = 6,
    width  = 6,
    type   = "metric",
    properties = {
      metrics = [
        ["AWS/Lambda", "Invocations", "FunctionName", "${var.api_lambda_name}", { label = "Requests" }],
        [".", "Errors", ".", ".", { color = "#d62728", yAxis = "left" }],
        [".", "ConcurrentExecutions", ".", ".", { stat = "Maximum", yAxis = "right" }],
        [".", "Throttles", ".", ".", { color = "#ff9896", label = "Throttles" }]
      ],
      period  = 60,
      region  = "${data.aws_region.current.name}",
      stat    = "Sum",
      title   = "API Requests & λ Concurrency ",
      view    = "timeSeries",
      stacked = false
    }
  })

  # Currently copies api_lambda_widget. Elected to not create another .tpl file 
  # as the metrics we care about for each might soon differ.
  api_auth_lambda_widget = jsonencode({
    height = 6,
    width  = 6,
    type   = "metric",
    properties = {
      metrics = [
        ["AWS/Lambda", "Invocations", "FunctionName", "${var.auth_lambda_name}", { label = "Requests" }],
        [".", "Errors", ".", ".", { color = "#d62728", yAxis = "left" }],
        [".", "ConcurrentExecutions", ".", ".", { stat = "Maximum", yAxis = "right" }],
        [".", "Throttles", ".", ".", { color = "#ff9896", label = "Throttles" }]
      ],
      period  = 60,
      region  = "${data.aws_region.current.name}",
      stat    = "Sum",
      title   = "Auth Requests & λ Concurrency ",
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
      region  = "${data.aws_region.current.name}",
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
      region  = "${data.aws_region.current.name}"
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
      region = "${data.aws_region.current.name}",
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
      region = "${data.aws_region.current.name}",
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

  # Should we add the submit event widgets to the dashboard?
  add_submit_event_widgets = var.submit_event_lambda_name != null

  submit_event_lambda_widget = jsonencode({
    height = 6,
    width  = 6,
    type   = "metric",
    properties = {
      metrics = [
        ["AWS/Lambda", "Invocations", "FunctionName", "${var.submit_event_lambda_name}", { label = "SubmitEvents" }],
        [".", "Errors", ".", ".", { color = "#d62728", yAxis = "left" }],
        [".", "ConcurrentExecutions", ".", ".", { stat = "Maximum", yAxis = "right" }],
        [".", "Throttles", ".", ".", { color = "#ff9896", label = "Throttles" }]
      ],
      period  = 60,
      region  = "${data.aws_region.current.name}",
      stat    = "Sum",
      title   = "Submit Event & λ Concurrency ",
      view    = "timeSeries",
      stacked = false
    }
  })

  submit_queue_widge = local.add_submit_event_widgets ? jsonencode({
    width = 6
    type  = "metric"
    properties = {
      title  = "${var.submit_event_queue[0]}: Age of Oldest Item"
      region = "${data.aws_region.current.name}"
      period = 60
      stat   = "Maximum"
      metrics = [
        [
          "AWS/SQS", "ApproximateNumberOfMessagesVisible",
          "QueueName", "${var.submit_event_queue[1]}", { stat = "Average" }
        ],
        [".", "ApproximateAgeOfOldestMessage", ".", ".", { yAxis = "right" }],
        [
          "AWS/SQS", "ApproximateNumberOfMessagesVisible",
          "QueueName", "${var.submit_event_queue[2]}", { stat = "Average", label = "dlq-approx-count" }
        ],
        [".", "ApproximateAgeOfOldestMessage", ".", ".", { yAxis = "right", label = "dlq-approx-age" }]
      ]
    }
  }) : jsonencode({})

  dashboard_body = <<JSON
  {
    "widgets": [
      ${local.title_glance},
      ${join(", ", local.pipeline_lambdas_widgets)},
      ${join(", ", local.queues_to_monitor_items)},

      ${local.title_api},
      ${local.api_auth_lambda_widget},
      ${local.api_lambda_widget},
      ${local.api_response_times},
      ${local.api_gateway_widget},

      ${local.title_dynamodb},
      ${local.dynamodb_datastore_rwcu_widget},
      ${local.dynamodb_datastore_errors_widget},

      ${local.title_system_capacity},
      ${local.total_concurrent_lambda}

      %{if local.add_submit_event_widgets}
      ,
      ${local.title_submit_event},
      ${local.submit_event_lambda_widget},
      ${local.submit_queue_widge}
      %{endif}
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
