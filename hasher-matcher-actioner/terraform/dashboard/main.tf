# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

# Due to limitations in terraform and the aws_cloudwatch_dashboard resource
# this files has loops and hard to parse JSON strings, apologies in advance.     
#   if something is broken it is usualy a missing or extra comma (or both) :'( 

locals {

  queues_to_monitor_items = [for queue_name in var.queues_to_monitor : <<EOF
{
  "width": 6,
  "type": "metric",
  "properties": {
    "title": "${queue_name}: Age of Oldest Item",
    "region": "${var.region}",
    "stat": "Maximum",
    "metrics": [
        [ 
          "AWS/SQS", "ApproximateNumberOfMessagesVisible", 
          "QueueName", "${queue_name}", { "stat": "Average" } 
        ],
        [ ".", "ApproximateAgeOfOldestMessage", ".", ".", { "yAxis": "right" } ]
    ]
  }
}
EOF
  ]

  lambdas_to_monitor_widgets = [for function_name in var.lambdas_to_monitor : <<EOF
{
  "type": "metric",
  "width": 6,
  "properties": {
    "title": "${function_name} λ Invocations",
    "region": "${var.region}",
    "stat": "Sum",
    "metrics": [
      [
        "AWS/Lambda", "Invocations",
        "FunctionName", "${function_name}"
      ],
      [ ".", "Errors", ".", ".", {"color": "#d62728" }],
      [ ".", "ConcurrentExecutions", ".", ".", { "stat": "Maximum" } ],
      [ ".", "Throttles", ".", ".", { "label": "Throttles", "yAxis": "right" } ]
    ]
  }
},
{
  "type": "metric",
  "width": 6,
  "properties": {
    "title": "${function_name} λ Duration",
    "region": "${var.region}",
    "stat": "Maximum",
    "metrics": [
      [
        "AWS/Lambda", "Duration",
        "FunctionName", "${function_name}", { "label": "p90" } 
      ],
      [ "...", { "label": "Av", "stat": "Average" } ]
    ]
  }
}
EOF
  ]

  total_concurrnet_lambda = <<EOF
{
  "width": 6,
  "type": "metric",
  "properties": {
      "title": "Total Concurrent  λ Executions",
      "region": "${var.region}",
      "stacked": true,
      "stat": "Maximum",
      "metrics": [ ${join(", ",
  [for function_name in var.lambdas_to_monitor : <<EOF
                            [ "AWS/Lambda", "ConcurrentExecutions", "FunctionName", "${function_name}" ]
                          EOF
  ]
)}
    ]
  }
}
EOF

api_gateway_widget = <<EOF
{
            "width": 6,
            "type": "metric",
            "region": "${var.region}",
            "properties": {
                "title": "API Gateway (${var.api_gateway_id})",
                "region": "${var.region}",
                "stat": "Sum",  
                "metrics": [
                    [ "AWS/ApiGateway", "4xx", "Stage", "$default", "ApiId", "${var.api_gateway_id}" ],
                    [ ".", "5xx", ".", ".", ".", "." ],
                    [ ".", "Count", ".", ".", ".", "." ],
                    [ ".", "DataProcessed", ".", ".", ".", ".", { "yAxis": "right" } ]
                ]
            }
}
EOF

datastore_widgets = <<EOF
{
  "width": 6,
  "type": "metric",
  "properties": {
      "title": "DynamoDB R/W Units (WIP: Consult ${var.datastore.name} for actual numbers)",
      "region": "${var.region}",
      "stat": "Average",
      "metrics": [
          [ "AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", "${var.datastore.name}", { "yAxis": "right" } ],
          [ ".", "ConsumedWriteCapacityUnits", ".", "." ],
          [ ".", "ConsumedReadCapacityUnits", ".", ".", "GlobalSecondaryIndexName", "GSI-2", { "yAxis": "right" } ],
          [ ".", "ConsumedWriteCapacityUnits", ".", ".", ".", "." ],
          [ ".", "ConsumedReadCapacityUnits", ".", ".", ".", "GSI-1", { "yAxis": "right" } ],
          [ ".", "ConsumedWriteCapacityUnits", ".", ".", ".", "." ]
      ]
  }
},
{
  "width": 6,
  "type": "metric",
  "properties": {
      "title": "DynamoDB Errors, Throttles, & Conflicts",
      "region": "${var.region}",
      "stat": "Sum",
      "metrics": [
          [ "AWS/DynamoDB", "ThrottledRequests", "TableName", "${var.datastore.name}", "Operation", "TransactWriteItems" ],
          [ ".", "SystemErrors", ".", ".", ".", "." ],
          [ ".", "ThrottledRequests", ".", ".", ".", "UpdateItem", { "yAxis": "left" } ],
          [ ".", "WriteThrottleEvents", ".", ".", "GlobalSecondaryIndexName", "GSI-2", { "yAxis": "left" } ],
          [ ".", "TransactionConflict", ".", ".", { "yAxis": "right" } ]
      ]
  }
}
EOF

dashboard_body = <<EOF
{
  "widgets": [
    ${join(", ", local.lambdas_to_monitor_widgets)},
    ${join(", ", local.queues_to_monitor_items)},
    ${local.total_concurrnet_lambda},
    ${local.api_gateway_widget},
    ${local.datastore_widgets}
    ]
}
EOF
}



resource "aws_cloudwatch_dashboard" "basic_dashboard" {
  dashboard_name = "${var.prefix}-dashboard"
  // tf converts numbers to strings when putting them in a list.
  // this strip quotes around numbers, so that {"value": "123"} turns into {"value": 123}
  dashboard_body = replace(local.dashboard_body, "/\"([0-9]+)\"/", "$1")
}
