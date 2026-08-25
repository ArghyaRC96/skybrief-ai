data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda_src"
  output_path = "${path.module}/weather_email_lambda.zip"
}

resource "aws_cloudwatch_log_group" "lambda_log_group" {
  name              = "/aws/lambda/${var.project_name}-lambda"
  retention_in_days = 14

  tags = {
    Name = "${var.project_name}-lambda-log-group"
  }
}

resource "aws_lambda_function" "weather_email_function" {
  function_name = "${var.project_name}-lambda"
  description   = "Daily weather forecast email service Lambda function"

  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  role    = aws_iam_role.lambda_execution_role.arn
  handler = "lambda_function.lambda_handler"
  runtime = "python3.12"

  timeout     = 60
  memory_size = 256

  environment {
    variables = {
      WEATHER_SECRET_NAME = aws_secretsmanager_secret.weather_config.name
    }
  }

  vpc_config {
    subnet_ids         = [aws_subnet.private.id]
    security_group_ids = [aws_security_group.lambda.id]
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_policy_attachment,
    aws_cloudwatch_log_group.lambda_log_group
  ]

  tags = {
    Name = "${var.project_name}-lambda"
  }
}