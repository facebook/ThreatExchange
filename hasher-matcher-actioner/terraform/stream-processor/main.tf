
# Define lambda
resource "aws_lambda_function" "stream_processor" {
  function_name = "${var.prefix}_stream_processor"
  package_type  = "Image"
  role          = aws_iam_role.stream_processor_lambda_role.arn
  image_uri     = var.lambda_docker_info.uri
  image_config {
    command = [var.lambda_docker_info.commands.stream_processor]
  }
  timeout     = 300
  memory_size = 512
  environment {
    variables = {
      DYNAMODB_TABLE                        = var.datastore.name
      HMA_CONFIG_TABLE                      = var.config_table.name
      MEASURE_PERFORMANCE                   = var.measure_performance ? "True" : "False"
    }
  }
  tags = merge(
    var.additional_tags,
    {
      Name = "StreamProcessor"
    }
  )
}

resource "aws_cloudwatch_log_group" "stream_processor" {
  name              = "/aws/lambda/${aws_lambda_function.stream_processor.function_name}"
  retention_in_days = var.log_retention_in_days
  tags = merge(
    var.additional_tags,
    {
      Name = "StreamProcessorLambdaLogGroup"
    }
  )
}

# Lambda permisions, this goes on for a while.
data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "stream_processor_lambda_role" {
  name_prefix        = "${var.prefix}_stream_processor"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags = merge(
    var.additional_tags,
    {
      Name = "StreamProcessorLambdaRole"
    }
  )
}

data "aws_iam_policy_document" "stream_processor_iam_policy_document" {
  statement {
    effect    = "Allow"
    actions   = ["dynamodb:GetItem", "dynamodb:Query", "dynamodb:Scan", "dynamodb:UpdateItem"]
    resources = ["${var.datastore.arn}*"]
  }
  statement {
    effect    = "Allow"
    actions   = ["dynamodb:GetItem", "dynamodb:Query", "dynamodb:Scan", "dynamodb:PutItem", "dynamodb:DeleteItem"]
    resources = [var.config_table.arn]
  }
  statement {
      effect  = "Allow"
      actions = ["dynamodb:GetRecords", "dynamodb:GetShardIterator", "dynamodb:DescribeStream", "dynamodb:ListShards", "dynamodb:ListStreams"]
      resources = [var.datastore.stream_arn]
  }
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]
    resources = ["${aws_cloudwatch_log_group.stream_processor.arn}:*"]
  }
}

resource "aws_iam_policy" "stream_processor_iam_policy" {
  name_prefix = "${var.prefix}_stream_processor_iam_policy"
  description = "Permissions for Stream Processor Lambda"
  policy      = data.aws_iam_policy_document.stream_processor_iam_policy_document.json
}

resource "aws_iam_role_policy_attachment" "stream_processor" {
  role       = aws_iam_role.stream_processor_lambda_role.name
  policy_arn = aws_iam_policy.stream_processor_iam_policy.arn
}
# Lambda permissions finally ends.

# Connect dynamodb -> lambda 
resource "aws_lambda_event_source_mapping" "primary_datastore_to_stream_processor" {
  event_source_arn  = var.datastore.stream_arn
#   event_source_arn = "arn:aws:dynamodb:us-east-1:521978645842:table/dipanjanm-HMADataStore/stream/2021-05-17T16:00:05.771"
  function_name     = aws_lambda_function.stream_processor.arn
  starting_position = "LATEST"
}