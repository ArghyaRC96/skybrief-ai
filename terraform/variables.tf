variable "aws_region" {
  description = "AWS region where resources will be created."
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Project name used for naming AWS resources."
  type        = string
  default     = "open-weather-email-service"
}

variable "openweather_api_key" {
  description = "OpenWeather API key used to fetch weather data."
  type        = string
  sensitive   = true
}

variable "sender_email" {
  description = "Verified sender email address for Amazon SES."
  type        = string
}

variable "sender_name" {
  description = "Sender display name for weather emails."
  type        = string
  default     = "Weather Forecast Service"
}

variable "receiver_email" {
  description = "Receiver email address for daily weather forecast emails."
  type        = string
}

variable "latitude" {
  description = "Latitude of the forecast location."
  type        = string
}

variable "longitude" {
  description = "Longitude of the forecast location."
  type        = string
}

variable "location_name" {
  description = "Human-readable location name."
  type        = string
}

variable "schedule_expression" {
  description = "Amazon EventBridge Scheduler expression for running the AWS Lambda function daily."
  type        = string
  default = "cron(0 8 * * ? *)"
}