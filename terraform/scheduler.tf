resource "aws_scheduler_schedule" "daily_weather_email" {
  name        = "${var.project_name}-daily-schedule"
  description = "Daily trigger for the weather forecast email Lambda function"

  schedule_expression          = var.schedule_expression
  schedule_expression_timezone = "Asia/Kolkata"

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = aws_lambda_function.weather_email_function.arn
    role_arn = aws_iam_role.scheduler_execution_role.arn
  }

  state = "ENABLED"
}