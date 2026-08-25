import json
import time
from datetime import date, datetime

from google import genai
from google.genai import types


PRIMARY_MODEL = "gemini-3.7-flash"
FALLBACK_MODEL = "gemini-3.6-flash"


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


def _is_transient_error(error):
    """
    Identify errors that are reasonable to retry.

    Typical transient HTTP status codes include:
    429, 500, 502, 503 and 504.
    """

    transient_status_codes = {
        429,
        500,
        502,
        503,
        504,
    }

    status_code = getattr(
        error,
        "status_code",
        None,
    )

    if status_code in transient_status_codes:
        return True

    error_text = str(error).upper()

    transient_markers = [
        "429",
        "500",
        "502",
        "503",
        "504",
        "RESOURCE_EXHAUSTED",
        "INTERNAL",
        "UNAVAILABLE",
        "TIMEOUT",
    ]

    return any(
        marker in error_text
        for marker in transient_markers
    )


def _generate_with_model(
    client,
    model_name,
    prompt,
):
    """
    Send one grounded generation request to Gemini.
    """

    response = client.models.generate_content(
        model=model_name,
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
            f"{model_name} returned an empty response."
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

    Strategy:
    1. Try Gemini 3.7 Flash once.
    2. If it fails for any reason, immediately use
       Gemini 3.6 Flash.
    """

    if not api_key:
        raise ValueError(
            "Gemini API key is required."
        )

    prompt = build_weather_prompt(
        current_summary=current_summary,
        forecast_df=forecast_df,
        daily_summary_df=daily_summary_df,
    )

    client = genai.Client(
        api_key=api_key
    )

    primary_error = None


    # --------------------------------------------------------
    # Primary model: one attempt only
    # --------------------------------------------------------

    try:

        text_result = _generate_with_model(
            client=client,
            model_name=PRIMARY_MODEL,
            prompt=prompt,
        )

        return {
            "text": text_result,
            "model": PRIMARY_MODEL,
            "used_fallback": False,
            "primary_error": None,
        }


    except Exception as error:

        primary_error = str(
            error
        )


    # --------------------------------------------------------
    # Immediate fallback
    # --------------------------------------------------------

    try:

        text_result = _generate_with_model(
            client=client,
            model_name=FALLBACK_MODEL,
            prompt=prompt,
        )

        return {
            "text": text_result,
            "model": FALLBACK_MODEL,
            "used_fallback": True,
            "primary_error": primary_error,
        }


    except Exception as fallback_error:

        raise RuntimeError(
            "SkyBrief AI insight generation failed. "
            f"Primary error: {primary_error}. "
            f"Fallback error: {fallback_error}"
        ) from fallback_error
