import json
import os
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime

import boto3


secrets_client = boto3.client("secretsmanager")
ses_client = boto3.client("ses")


def get_secret(secret_name):
    """
    Read configuration values from AWS Secrets Manager.

    AWS Secrets Manager stores sensitive values such as:
    - OpenWeather API key
    - Sender email
    - Receiver email
    - Location configuration
    """

    response = secrets_client.get_secret_value(SecretId=secret_name)
    secret_string = response["SecretString"]

    return json.loads(secret_string)


def fetch_json(url, params):
    """
    Make an HTTP GET request and return JSON response.
    urllib is used instead of requests to keep the Lambda package lightweight.
    """

    query_string = urllib.parse.urlencode(params)
    full_url = f"{url}?{query_string}"

    with urllib.request.urlopen(full_url, timeout=20) as response:
        response_body = response.read().decode("utf-8")

    return json.loads(response_body)


def fetch_current_weather(latitude, longitude, api_key, units="metric", language="en"):
    """
    Fetch current weather data from OpenWeather API.
    """

    url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": api_key,
        "units": units,
        "lang": language
    }

    return fetch_json(url, params)


def fetch_forecast_weather(latitude, longitude, api_key, units="metric", language="en"):
    """
    Fetch 5-day forecast data from OpenWeather API.
    The forecast API returns data at 3-hour intervals.
    """

    url = "https://api.openweathermap.org/data/2.5/forecast"

    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": api_key,
        "units": units,
        "lang": language
    }

    return fetch_json(url, params)


def convert_to_local_datetime(timestamp, timezone_offset_seconds):
    """
    Convert Unix timestamp to local datetime using city timezone offset.
    """

    return datetime.utcfromtimestamp(timestamp + timezone_offset_seconds)


def build_current_weather_summary(current_data, location_name, timezone_offset_seconds):
    """
    Convert current weather response into a clean dictionary.
    """

    return {
        "location": location_name,
        "timestamp": convert_to_local_datetime(
            current_data["dt"],
            timezone_offset_seconds
        ).strftime("%Y-%m-%d %H:%M:%S"),
        "temperature_celsius": current_data["main"].get("temp"),
        "feels_like_celsius": current_data["main"].get("feels_like"),
        "humidity_percent": current_data["main"].get("humidity"),
        "pressure_hpa": current_data["main"].get("pressure"),
        "wind_speed_mps": current_data["wind"].get("speed"),
        "cloudiness_percent": current_data["clouds"].get("all"),
        "weather_main": current_data["weather"][0].get("main"),
        "weather_description": current_data["weather"][0].get("description")
    }


def build_daily_forecast_summary(forecast_data, timezone_offset_seconds):
    """
    Convert 3-hour forecast records into daily summary rows.

    This avoids pandas dependency inside Lambda and keeps deployment lightweight.
    """

    grouped_data = {}

    for item in forecast_data["list"]:
        local_datetime = convert_to_local_datetime(
            item["dt"],
            timezone_offset_seconds
        )

        date_key = local_datetime.date().isoformat()

        if date_key not in grouped_data:
            grouped_data[date_key] = {
                "temperatures": [],
                "humidity_values": [],
                "wind_speed_values": [],
                "rain_probability_values": [],
                "cloudiness_values": [],
                "weather_descriptions": []
            }

        grouped_data[date_key]["temperatures"].append(item["main"].get("temp"))
        grouped_data[date_key]["humidity_values"].append(item["main"].get("humidity"))
        grouped_data[date_key]["wind_speed_values"].append(item["wind"].get("speed"))
        grouped_data[date_key]["rain_probability_values"].append(item.get("pop", 0))
        grouped_data[date_key]["cloudiness_values"].append(item["clouds"].get("all"))
        grouped_data[date_key]["weather_descriptions"].append(
            item["weather"][0].get("description")
        )

    daily_summary = []

    for date_key, values in grouped_data.items():
        temperatures = values["temperatures"]
        humidity_values = values["humidity_values"]
        wind_speed_values = values["wind_speed_values"]
        rain_probability_values = values["rain_probability_values"]
        cloudiness_values = values["cloudiness_values"]
        weather_descriptions = values["weather_descriptions"]

        most_common_description = Counter(weather_descriptions).most_common(1)[0][0]

        daily_summary.append({
            "date": date_key,
            "temp_min_celsius": min(temperatures),
            "temp_max_celsius": max(temperatures),
            "temp_avg_celsius": sum(temperatures) / len(temperatures),
            "humidity_avg_percent": sum(humidity_values) / len(humidity_values),
            "wind_speed_avg_mps": sum(wind_speed_values) / len(wind_speed_values),
            "rain_probability_max_percent": max(rain_probability_values) * 100,
            "cloudiness_avg_percent": sum(cloudiness_values) / len(cloudiness_values),
            "weather_description": most_common_description
        })

    return daily_summary


def build_daily_rows_html(daily_summary):
    """
    Create HTML table rows for daily forecast summary.
    """

    rows_html = ""

    for row in daily_summary:
        rows_html += f"""
        <tr>
            <td style="padding:10px; border:1px solid #e5e7eb;">{row["date"]}</td>
            <td style="padding:10px; border:1px solid #e5e7eb;">{row["temp_min_celsius"]:.1f}°C</td>
            <td style="padding:10px; border:1px solid #e5e7eb;">{row["temp_max_celsius"]:.1f}°C</td>
            <td style="padding:10px; border:1px solid #e5e7eb;">{row["temp_avg_celsius"]:.1f}°C</td>
            <td style="padding:10px; border:1px solid #e5e7eb;">{row["humidity_avg_percent"]:.1f}%</td>
            <td style="padding:10px; border:1px solid #e5e7eb;">{row["rain_probability_max_percent"]:.1f}%</td>
            <td style="padding:10px; border:1px solid #e5e7eb;">{row["weather_description"].title()}</td>
        </tr>
        """

    return rows_html


def build_html_weather_report(current_summary, daily_summary, generated_at):
    """
    Build final HTML email report.
    """

    daily_rows_html = build_daily_rows_html(daily_summary)

    html_report = f"""
    <html>
      <body style="margin:0; padding:0; background-color:#f4f7fb; font-family:Arial, sans-serif;">
        <div style="max-width:900px; margin:30px auto; background-color:#ffffff; border-radius:14px; padding:28px; border:1px solid #e5e7eb;">

          <h2 style="color:#1f4e79; margin-bottom:6px;">
            Daily Weather Forecast Report
          </h2>

          <p style="color:#6b7280; margin-top:0;">
            Location: <b>{current_summary["location"]}</b><br>
            Generated at: <b>{generated_at}</b>
          </p>

          <div style="background-color:#eff6ff; border-left:5px solid #2563eb; padding:16px; margin:22px 0; border-radius:8px;">
            <h3 style="margin-top:0; color:#1e3a8a;">Current Weather Summary</h3>
            <p style="font-size:15px; color:#374151; line-height:1.7;">
              Current condition is <b>{current_summary["weather_description"].title()}</b>.
              Temperature is <b>{current_summary["temperature_celsius"]}°C</b>, feels like
              <b>{current_summary["feels_like_celsius"]}°C</b>. Humidity is
              <b>{current_summary["humidity_percent"]}%</b> with wind speed of
              <b>{current_summary["wind_speed_mps"]} m/s</b>.
            </p>
          </div>

          <h3 style="color:#111827;">Current Weather Details</h3>

          <table style="border-collapse:collapse; width:100%; margin-top:12px; font-size:14px;">
            <tr>
              <td style="padding:10px; border:1px solid #e5e7eb; background-color:#f9fafb;"><b>Temperature</b></td>
              <td style="padding:10px; border:1px solid #e5e7eb;">{current_summary["temperature_celsius"]}°C</td>
            </tr>
            <tr>
              <td style="padding:10px; border:1px solid #e5e7eb; background-color:#f9fafb;"><b>Feels Like</b></td>
              <td style="padding:10px; border:1px solid #e5e7eb;">{current_summary["feels_like_celsius"]}°C</td>
            </tr>
            <tr>
              <td style="padding:10px; border:1px solid #e5e7eb; background-color:#f9fafb;"><b>Humidity</b></td>
              <td style="padding:10px; border:1px solid #e5e7eb;">{current_summary["humidity_percent"]}%</td>
            </tr>
            <tr>
              <td style="padding:10px; border:1px solid #e5e7eb; background-color:#f9fafb;"><b>Wind Speed</b></td>
              <td style="padding:10px; border:1px solid #e5e7eb;">{current_summary["wind_speed_mps"]} m/s</td>
            </tr>
            <tr>
              <td style="padding:10px; border:1px solid #e5e7eb; background-color:#f9fafb;"><b>Cloudiness</b></td>
              <td style="padding:10px; border:1px solid #e5e7eb;">{current_summary["cloudiness_percent"]}%</td>
            </tr>
          </table>

          <h3 style="color:#111827; margin-top:28px;">5-Day Daily Forecast Summary</h3>

          <table style="border-collapse:collapse; width:100%; margin-top:12px; font-size:13px;">
            <tr style="background-color:#1f4e79; color:#ffffff;">
              <th style="padding:10px; border:1px solid #e5e7eb;">Date</th>
              <th style="padding:10px; border:1px solid #e5e7eb;">Min Temp</th>
              <th style="padding:10px; border:1px solid #e5e7eb;">Max Temp</th>
              <th style="padding:10px; border:1px solid #e5e7eb;">Avg Temp</th>
              <th style="padding:10px; border:1px solid #e5e7eb;">Avg Humidity</th>
              <th style="padding:10px; border:1px solid #e5e7eb;">Max Rain Probability</th>
              <th style="padding:10px; border:1px solid #e5e7eb;">Likely Condition</th>
            </tr>
            {daily_rows_html}
          </table>

          <p style="margin-top:24px; color:#374151; font-size:15px;">
            Regards,<br>
            <b>Weather Forecast Email Service</b>
          </p>

        </div>
      </body>
    </html>
    """

    return html_report


def format_sender(sender_email, sender_name):
    """
    Format sender value for Amazon SES.
    """

    if sender_name:
        return f"{sender_name} <{sender_email}>"

    return sender_email


def send_email_with_ses(sender_email, sender_name, receiver_email, subject, html_body):
    """
    Send HTML email using Amazon SES.

    SES means Simple Email Service.
    It is AWS's production-grade email sending service.
    """

    source = format_sender(sender_email, sender_name)

    response = ses_client.send_email(
        Source=source,
        Destination={
            "ToAddresses": [receiver_email]
        },
        Message={
            "Subject": {
                "Data": subject,
                "Charset": "UTF-8"
            },
            "Body": {
                "Html": {
                    "Data": html_body,
                    "Charset": "UTF-8"
                },
                "Text": {
                    "Data": "This email contains a weather forecast report. Please view it in an HTML-supported email client.",
                    "Charset": "UTF-8"
                }
            }
        }
    )

    return response


def lambda_handler(event, context):
    """
    Main AWS Lambda entry point.

    This function:
    1. Reads secrets from AWS Secrets Manager
    2. Fetches weather data from OpenWeather API
    3. Builds an HTML weather report
    4. Sends the report using Amazon SES
    """

    secret_name = os.environ.get("WEATHER_SECRET_NAME")

    if not secret_name:
        raise ValueError("WEATHER_SECRET_NAME environment variable is missing.")

    config = get_secret(secret_name)

    openweather_api_key = config["openweather_api_key"]
    sender_email = config["sender_email"]
    sender_name = config.get("sender_name", "Weather Forecast Service")
    receiver_email = config["receiver_email"]

    latitude = config["latitude"]
    longitude = config["longitude"]
    location_name = config.get("location_name", "Configured Location")

    units = config.get("units", "metric")
    language = config.get("language", "en")

    current_data = fetch_current_weather(
        latitude=latitude,
        longitude=longitude,
        api_key=openweather_api_key,
        units=units,
        language=language
    )

    forecast_data = fetch_forecast_weather(
        latitude=latitude,
        longitude=longitude,
        api_key=openweather_api_key,
        units=units,
        language=language
    )

    timezone_offset_seconds = forecast_data.get("city", {}).get(
        "timezone",
        current_data.get("timezone", 0)
    )

    current_summary = build_current_weather_summary(
        current_data=current_data,
        location_name=location_name,
        timezone_offset_seconds=timezone_offset_seconds
    )

    daily_summary = build_daily_forecast_summary(
        forecast_data=forecast_data,
        timezone_offset_seconds=timezone_offset_seconds
    )

    generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    html_report = build_html_weather_report(
        current_summary=current_summary,
        daily_summary=daily_summary,
        generated_at=generated_at
    )

    subject = f"Daily Weather Forecast Report - {location_name}"

    email_response = send_email_with_ses(
        sender_email=sender_email,
        sender_name=sender_name,
        receiver_email=receiver_email,
        subject=subject,
        html_body=html_report
    )

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Weather forecast email sent successfully.",
            "location": location_name,
            "receiver_email": receiver_email,
            "ses_message_id": email_response.get("MessageId"),
            "generated_at": generated_at
        })
    }

'''

The notebook version generates charts for visual demonstration.
The AWS Lambda production version keeps the deployment lightweight 
by sending a structured HTML forecast report. Chart generation can be added later
using a Lambda Layer or by storing generated images in Amazon S3.

'''