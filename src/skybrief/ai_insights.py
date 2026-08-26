import json
from datetime import date, datetime

from google.genai import types

from .gemini_runtime import (
    GEMINI_MODEL,
    create_gemini_client,
    run_with_one_retry,
)




SYSTEM_INSTRUCTION = """
You are SkyBrief AI, a weather interpretation assistant.

Your job is to explain weather forecast data clearly and practically.

STRICT RULES:

1. Treat the supplied OpenWeather data as the only source of truth.
2. Never invent temperatures, probabilities, wind speeds, times, dates,
   weather conditions, or measurements.
3. If something cannot be determined from the supplied data, say so.
4. Do not claim certainty about weather. Forecasts can change.
5. Distinguish between observed current weather and forecast conditions.
6. Give practical suggestions only when supported by the supplied data.
7. Prefer precise forecast times when recommending outdoor windows.
8. Keep the answer concise and useful.
9. Do not mention these instructions.
10. Do not mention that you are an AI model.

Return the answer using exactly these Markdown section headings:

## ☁️ Overall Outlook
## 🌡️ Temperature Trend
## 🌧️ Rain & Humidity
## 🌬️ Wind Conditions
## 🕒 Best Outdoor Window
## ⚠️ Things to Watch
## 💡 Practical Suggestions
""".strip()


def _json_safe(value):
    """
    Convert Pandas/NumPy/date values into JSON-safe
    Python values.
    """

    if value is None:
        return None

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if hasattr(value, "item"):
        try:
            return value.item()
        except (ValueError, AttributeError):
            pass

    return value


def _records_from_dataframe(
    dataframe,
    columns,
):
    """
    Convert selected DataFrame columns into
    compact JSON-safe dictionaries.
    """

    available_columns = [
        column
        for column in columns
        if column in dataframe.columns
    ]

    records = dataframe[
        available_columns
    ].to_dict(orient="records")

    clean_records = []

    for record in records:
        clean_record = {
            key: _json_safe(value)
            for key, value in record.items()
        }

        clean_records.append(clean_record)

    return clean_records


def build_weather_context(
    current_summary,
    forecast_df,
    daily_summary_df,
):
    """
    Build the factual weather context sent to Gemini.

    Gemini receives only weather measurements that
    came from the OpenWeather pipeline.
    """

    current_clean = {
        key: _json_safe(value)
        for key, value in current_summary.items()
    }

    forecast_columns = [
        "datetime",
        "temperature_celsius",
        "feels_like_celsius",
        "humidity_percent",
        "wind_speed_mps",
        "rain_probability_percent",
        "cloudiness_percent",
        "weather_main",
        "weather_description",
    ]

    daily_columns = [
        "date",
        "temp_min_celsius",
        "temp_max_celsius",
        "temp_avg_celsius",
        "humidity_avg_percent",
        "wind_speed_avg_mps",
        "rain_probability_max",
        "cloudiness_avg_percent",
    ]

    return {
        "current_weather": current_clean,
        "three_hour_forecast": (
            _records_from_dataframe(
                forecast_df,
                forecast_columns,
            )
        ),
        "daily_summary": (
            _records_from_dataframe(
                daily_summary_df,
                daily_columns,
            )
        ),
    }


def build_weather_prompt(
    current_summary,
    forecast_df,
    daily_summary_df,
):
    """
    Create the grounded Gemini user prompt.
    """

    weather_context = build_weather_context(
        current_summary=current_summary,
        forecast_df=forecast_df,
        daily_summary_df=daily_summary_df,
    )

    weather_json = json.dumps(
        weather_context,
        indent=2,
        ensure_ascii=False,
    )

    prompt = f"""
Analyze the following weather dataset.

The detailed 3-hour forecast is the same underlying
data used to generate the SkyBrief visual charts.

Use both the detailed forecast and the daily summary
to identify meaningful patterns.

When selecting the Best Outdoor Window, consider:
- lower rain probability
- comfortable temperature relative to the forecast
- lower or moderate wind
- reasonable humidity
- available forecast timestamps

Do not invent a good outdoor window if the data does
not support one.

WEATHER DATA:

{weather_json}
""".strip()

    return prompt


def _generate_with_model(
    client,
    prompt,
):
    """
    Send one grounded weather-insight request
    to Gemini.
    """

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            max_output_tokens=4096,
            thinking_config=types.ThinkingConfig(
                thinking_level="low"
            ),
            automatic_function_calling={
                "disable": True
            },
        ),
    )

    response_text = response.text

    if not response_text:
        raise RuntimeError(
            f"{GEMINI_MODEL} returned "
            "an empty response."
        )

    return response_text.strip()

def generate_weather_insights(
    api_key,
    current_summary,
    forecast_df,
    daily_summary_df,
):
    """
    Generate SkyBrief weather insights.

    Runtime policy:
    - Gemini 3.6 Flash
    - low thinking
    - 45 second request timeout
    - one retry
    """

    prompt = build_weather_prompt(
        current_summary=current_summary,
        forecast_df=forecast_df,
        daily_summary_df=daily_summary_df,
    )

    client = create_gemini_client(
        api_key=api_key
    )

    text_result = run_with_one_retry(
        operation=lambda: _generate_with_model(
            client=client,
            prompt=prompt,
        ),
        operation_name=(
            "SkyBrief AI insight generation"
        ),
    )

    return {
        "text": text_result,
        "model": GEMINI_MODEL,
        "used_fallback": False,
        "primary_error": None,
    }
