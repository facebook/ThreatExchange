# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

### Lambda for eat_memory ###

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

resource "aws_lambda_function" "eat_memory" {
  function_name = "${var.prefix}_eat_memory"
  package_type  = "Image"
  role          = aws_iam_role.eat_memory.arn
  image_uri     = var.lambda_docker_info.uri
  image_config {
    command = ["hmalib.lambdas.eat_memory.lambda_handler"]
  }

  # Timeout is kept less than the fetch frequency. Right now, fetch frequency is
  # 15 minutes, so we timeout at 12. The more this value, the more time every
  # single fetch has to complete.
  # TODO: make this computed from var.fetch_frequency.
  timeout = 60 * 12

  memory_size = 128
environment {
    variables = {  FRANKLIN="franklin"
}
}
}


resource "aws_cloudwatch_log_group" "eat_memory" {
  name              = "/aws/lambda/${aws_lambda_function.eat_memory.function_name}"
  tags = merge(
    var.additional_tags,
    {
      Name = "FetcherLambdaLogGroup"
    }
  )
}

resource "aws_iam_role" "eat_memory" {
  name_prefix        = "${var.prefix}_eat_memory"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags = merge(
    var.additional_tags,
    {
      Name = "EatMemoryLambdaRole"
    }
  )
}

data "aws_iam_policy_document" "eat_memory" {

  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]
    resources = ["${aws_cloudwatch_log_group.eat_memory.arn}:*"]
  }

}

resource "aws_iam_policy" "eat_memory" {
  name_prefix = "${var.prefix}_eat_memory_role_policy"
  description = "Permissions for Fetcher Lambda"
  policy      = data.aws_iam_policy_document.eat_memory.json
}

resource "aws_iam_role_policy_attachment" "eat_memory" {
  role       = aws_iam_role.eat_memory.name
  policy_arn = aws_iam_policy.eat_memory.arn
}

