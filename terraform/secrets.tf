resource "aws_secretsmanager_secret" "weather_config" {
  name        = "${var.project_name}-weather-config"
  description = "Configuration secrets for the daily weather forecast email service"

  tags = {
    Name = "${var.project_name}-weather-config"
  }
}

resource "aws_secretsmanager_secret_version" "weather_config_version" {
  secret_id = aws_secretsmanager_secret.weather_config.id

  secret_string = jsonencode({
    openweather_api_key = var.openweather_api_key
    sender_email        = var.sender_email
    sender_name         = var.sender_name
    receiver_email      = var.receiver_email
    latitude            = var.latitude
    longitude           = var.longitude
    location_name       = var.location_name
    units               = "metric"
    language            = "en"
  })
}