variable "matches_sns_topic_arn" {
  description = "ARN for the topic that collects matches from matchers."
  type        = string
}

variable "lambda_docker_info" {
  description = "Docker container information for lambda functions"
  type = object({
    uri = string
    commands = object({
      action_evaluator = string
      action_performer = string
      reactioner       = string
    })
  })
}

variable "prefix" {
  description = "Prefix to use for resource names"
  type        = string
}

variable "log_retention_in_days" {
  description = "How long to retain cloudwatch logs for lambda functions in days"
  type        = number
}

variable "additional_tags" {
  description = "Additional resource tags"
  type        = map(string)
  default     = {}
}

variable "measure_performance" {
  description = "Send metrics to cloudwatch. Useful for benchmarking, but can incur costs. Set to string True for this to work."
  type        = bool
  default     = false
}

variable "te_api_token_secret" {
  description = "The aws secret where the ThreatExchange API token is stored"
  type = object({
    name = string
    arn  = string
  })
}

variable "config_table" {
  description = "The name and arn of the DynamoDB table used for persisting configs."
  type = object({
    arn  = string
    name = string
  })
}
