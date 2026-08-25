from datetime import datetime, timedelta, timezone

import pandas as pd
import requests


CURRENT_WEATHER_URL = (
    "https://api.openweathermap.org/data/2.5/weather"
)

FORECAST_WEATHER_URL = (
    "https://api.openweathermap.org/data/2.5/forecast"
)


def fetch_current_weather(
    latitude,
    longitude,
    api_key,
    units="metric",
    language="en",
):
    """
    Fetch current weather data from OpenWeather.
    """

    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": api_key,
        "units": units,
        "lang": language,
    }

    response = requests.get(
        CURRENT_WEATHER_URL,
        params=params,
        timeout=20,
    )

    response.raise_for_status()

    return response.json()


def fetch_forecast_weather(
    latitude,
    longitude,
    api_key,
    units="metric",
    language="en",
):
    """
    Fetch OpenWeather 5-day forecast.

    The free forecast endpoint returns one forecast
    record every 3 hours.
    """

    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": api_key,
        "units": units,
        "lang": language,
    }

    response = requests.get(
        FORECAST_WEATHER_URL,
        params=params,
        timeout=20,
    )

    response.raise_for_status()

    return response.json()


def convert_to_local_datetime(
    timestamp,
    timezone_offset_seconds,
):
    """
    Convert Unix UTC timestamp to the forecast
    location's local datetime.
    """

    utc_datetime = datetime.fromtimestamp(
        timestamp,
        tz=timezone.utc,
    )

    local_datetime = utc_datetime + timedelta(
        seconds=timezone_offset_seconds
    )

    return local_datetime.replace(tzinfo=None)


def build_current_weather_summary(
    current_data,
    location_name,
    timezone_offset_seconds,
):
    """
    Convert OpenWeather current response into
    a clean dictionary.
    """

    return {
        "location": location_name,
        "timestamp": convert_to_local_datetime(
            current_data["dt"],
            timezone_offset_seconds,
        ),
        "temperature_celsius": (
            current_data["main"].get("temp")
        ),
        "feels_like_celsius": (
            current_data["main"].get("feels_like")
        ),
        "humidity_percent": (
            current_data["main"].get("humidity")
        ),
        "pressure_hpa": (
            current_data["main"].get("pressure")
        ),
        "wind_speed_mps": (
            current_data["wind"].get("speed")
        ),
        "cloudiness_percent": (
            current_data["clouds"].get("all")
        ),
        "weather_main": (
            current_data["weather"][0].get("main")
        ),
        "weather_description": (
            current_data["weather"][0].get(
                "description"
            )
        ),
    }


def build_forecast_dataframe(
    forecast_data,
    timezone_offset_seconds,
):
    """
    Convert OpenWeather 3-hour forecast records
    into a Pandas DataFrame.
    """

    records = []

    for item in forecast_data["list"]:
        records.append(
            {
                "datetime": convert_to_local_datetime(
                    item["dt"],
                    timezone_offset_seconds,
                ),
                "temperature_celsius": (
                    item["main"].get("temp")
                ),
                "feels_like_celsius": (
                    item["main"].get("feels_like")
                ),
                "humidity_percent": (
                    item["main"].get("humidity")
                ),
                "pressure_hpa": (
                    item["main"].get("pressure")
                ),
                "wind_speed_mps": (
                    item["wind"].get("speed")
                ),
                "cloudiness_percent": (
                    item["clouds"].get("all")
                ),
                "pop_probability": item.get(
                    "pop",
                    0,
                ),
                "weather_main": (
                    item["weather"][0].get("main")
                ),
                "weather_description": (
                    item["weather"][0].get(
                        "description"
                    )
                ),
            }
        )

    forecast_df = pd.DataFrame(records)

    forecast_df["rain_probability_percent"] = (
        forecast_df["pop_probability"] * 100
    )

    forecast_df["date"] = (
        forecast_df["datetime"].dt.date
    )

    return forecast_df


def build_daily_summary(forecast_df):
    """
    Aggregate the 3-hour forecast into
    daily weather statistics.
    """

    daily_summary_df = (
        forecast_df.groupby("date")
        .agg(
            temp_min_celsius=(
                "temperature_celsius",
                "min",
            ),
            temp_max_celsius=(
                "temperature_celsius",
                "max",
            ),
            temp_avg_celsius=(
                "temperature_celsius",
                "mean",
            ),
            humidity_avg_percent=(
                "humidity_percent",
                "mean",
            ),
            wind_speed_avg_mps=(
                "wind_speed_mps",
                "mean",
            ),
            rain_probability_max=(
                "rain_probability_percent",
                "max",
            ),
            cloudiness_avg_percent=(
                "cloudiness_percent",
                "mean",
            ),
        )
        .reset_index()
    )

    return daily_summary_df


def get_weather_report_data(
    latitude,
    longitude,
    location_name,
    api_key,
    units="metric",
    language="en",
):
    """
    Main reusable weather pipeline.

    Returns:
    - raw current response
    - raw forecast response
    - current summary dictionary
    - detailed forecast DataFrame
    - daily summary DataFrame
    """

    current_data = fetch_current_weather(
        latitude=latitude,
        longitude=longitude,
        api_key=api_key,
        units=units,
        language=language,
    )

    forecast_data = fetch_forecast_weather(
        latitude=latitude,
        longitude=longitude,
        api_key=api_key,
        units=units,
        language=language,
    )

    timezone_offset_seconds = (
        forecast_data
        .get("city", {})
        .get(
            "timezone",
            current_data.get("timezone", 0),
        )
    )

    current_summary = (
        build_current_weather_summary(
            current_data=current_data,
            location_name=location_name,
            timezone_offset_seconds=(
                timezone_offset_seconds
            ),
        )
    )

    forecast_df = build_forecast_dataframe(
        forecast_data=forecast_data,
        timezone_offset_seconds=(
            timezone_offset_seconds
        ),
    )

    daily_summary_df = build_daily_summary(
        forecast_df
    )

    return {
        "current_data": current_data,
        "forecast_data": forecast_data,
        "current_summary": current_summary,
        "forecast_df": forecast_df,
        "daily_summary_df": daily_summary_df,
    }
