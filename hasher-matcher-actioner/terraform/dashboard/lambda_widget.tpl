${jsonencode({
  width  = 6
  type   = "metric"
  properties = {
    title  = "${lambda_title} λ Invocations & Duration"
    region = "${region}"
    period = 60
    stat   = "Sum"
    metrics = [
      [
        "AWS/Lambda", "Invocations",
        "FunctionName", "${lambda_name}"
      ],
      [".", "Errors", ".", ".", { color = "#d62728" }],
      [".", "ConcurrentExecutions", ".", ".", { stat = "Maximum" }],
      [".", "Throttles", ".", ".", { label = "Throttles", color = "#ff9896" }],
      [".", "Duration", ".", ".", { stat = "p90", label = "p90", yAxis = "right" }],
      ["...", { label = "Av", stat = "Average", yAxis = "right", color = "#ff7f0e" }]
    ]
  }
})}
