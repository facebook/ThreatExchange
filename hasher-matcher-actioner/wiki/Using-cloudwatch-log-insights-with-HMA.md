Say you have unexplained errors in your cloudwatch dashboard. You want to dive deeper, understand what these errors are and how to go about fixing them. This page explains what you could be doing.

# CloudWatch Insights

From [Amazon's documentation](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AnalyzingLogData.html):

> CloudWatch Logs Insights enables you to interactively search and analyze your log data in Amazon CloudWatch Logs. You can perform queries to help you more efficiently and effectively respond to operational issues. If an issue occurs, you can use CloudWatch Logs Insights to identify potential causes and validate deployed fixes. 

# Querying CloudWatch Insights

Open the [cloudwatch home](https://console.aws.amazon.com/cloudwatch/home) on the AWS console, and click on "Insights" under "Logs" in the left sidebar. Here, select the log groups you are interested in. Most often the log groups you are interested in are going to be from the submission, hashing, matching and actioning components. 

They will look like:
* `/aws/lambda/<your-prefix>_api_root`
* `/aws/lambda/<your-prefix>_pdq_hasher`
* `/aws/lambda/<your-prefix>_pdq_matcher`
* `/aws/lambda/<your-prefix>_action_evaluator`
* `/aws/lambda/<your-prefix>_action_performer`

Once you have selected the important log groups, select a time range that you are interested in. If you are debugging an ongoing issues, you can use the 1H (Last 1 hour), 3H (Last 3 hours) toggles.

# Sample queries to identify common errors

Get a measure of all errors across various log groups.

```
fields @timestamp, @message
| sort @timestamp desc
| filter substr(@message, 0, 7) == "[ERROR]"
| filter !strcontains(@message, "Couldn't report metrics to cloudwatch")
| parse @message "[ERROR] *: *" as loggingMessage
| stats count() by loggingMessage
```