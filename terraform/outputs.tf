output "vpc_id" {
  description = "ID of the created VPC - Virtual Private Cloud."
  value       = aws_vpc.main.id
}

output "public_subnet_id" {
  description = "ID of the created public subnet."
  value       = aws_subnet.public.id
}

output "private_subnet_id" {
  description = "ID of the created private subnet."
  value       = aws_subnet.private.id
}

output "lambda_function_name" {
  description = "Name of the AWS Lambda function."
  value       = aws_lambda_function.weather_email_function.function_name
}

output "lambda_function_arn" {
  description = "ARN of the AWS Lambda function."
  value       = aws_lambda_function.weather_email_function.arn
}

output "secret_name" {
  description = "Name of the AWS Secrets Manager secret."
  value       = aws_secretsmanager_secret.weather_config.name
}

output "scheduler_name" {
  description = "Name of the Amazon EventBridge Scheduler schedule."
  value       = aws_scheduler_schedule.daily_weather_email.name
}

output "ses_sender_identity" {
  description = "Amazon SES - Simple Email Service sender identity."
  value       = aws_ses_email_identity.sender.email
}