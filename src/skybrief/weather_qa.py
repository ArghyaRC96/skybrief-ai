
from google.genai import types

from .gemini_runtime import (
    GEMINI_MODEL,
    create_gemini_client,
    run_with_one_retry,
)




QA_SYSTEM_INSTRUCTION = """
You are Ask the Sky, the conversational weather planner
inside SkyBrief AI.

Use ONLY the supplied OpenWeather forecast data.

TONE:
- Warm, energetic, conversational and slightly funky.
- Professional enough for a polished weather product.
- Never sound robotic, blunt or clinical.
- Give useful reasoning, not just a yes/no verdict.

CONVERSATION:
- Treat previous exchanges as one continuing conversation.
- Resolve references like "it", "that time", "another day",
  "the picnic", or "the football match" from prior context.
- Do not repeat an offer for something you already provided.
- If the user asks for a better time window and you provide one,
  DO NOT finish by offering to provide another better time window.

ANSWER STYLE:
- Usually 100–180 words when explanation is useful.
- Start with a natural verdict.
- Explain why using relevant forecast evidence.
- Give a practical recommendation when appropriate.
- Avoid unnecessary repetition.

FACTUAL RULES:
- Never invent weather measurements.
- Never invent forecast timestamps.
- Mention only values supported by the supplied data.
- If requested time is outside the forecast, say so.
- "Safe" means weather suitability only.
- Never guarantee safety.
- Use 12-hour AM/PM time without seconds.
- If unrelated to weather, politely say SkyBrief handles
  weather-planning questions only.

QUESTION-LIMIT RULE:
The prompt will tell you how many questions remain.

If ZERO questions remain after the current answer:
- DO NOT invite another question.
- DO NOT say "if you want, I can..."
- DO NOT offer another recommendation for a future turn.
- Finish naturally with:
  "That wraps your 3/3 SkyBrief questions for this forecast. ☁️"

If questions remain:
- You may offer ONE useful follow-up idea only when it genuinely
  adds value.
- Never offer something that the current answer already provided.
""".strip()


def _compact_weather_context(
    current_summary,
    forecast_df,
    daily_summary_df,
):
    """
    Compact weather context keeps Gemini input usage controlled.
    """

    current = (
        f"CURRENT | "
        f"{current_summary.get('timestamp')} | "
        f"{current_summary.get('temperature_celsius')}C | "
        f"feels {current_summary.get('feels_like_celsius')}C | "
        f"humidity {current_summary.get('humidity_percent')}% | "
        f"wind {current_summary.get('wind_speed_mps')}m/s | "
        f"{current_summary.get('weather_description')}"
    )

    forecast_lines = []

    for row in forecast_df.itertuples():
        forecast_lines.append(
            " | ".join(
                [
                    row.datetime.strftime(
                        "%Y-%m-%d %I:%M %p"
                    ),
                    f"{row.temperature_celsius:.1f}C",
                    f"feels {row.feels_like_celsius:.1f}C",
                    f"rain {row.rain_probability_percent:.0f}%",
                    f"humidity {row.humidity_percent:.0f}%",
                    f"wind {row.wind_speed_mps:.1f}m/s",
                    str(row.weather_description),
                ]
            )
        )

    daily_lines = []

    for row in daily_summary_df.itertuples():
        daily_lines.append(
            " | ".join(
                [
                    str(row.date),
                    (
                        f"{row.temp_min_celsius:.1f}-"
                        f"{row.temp_max_celsius:.1f}C"
                    ),
                    (
                        f"rain max "
                        f"{row.rain_probability_max:.0f}%"
                    ),
                    (
                        f"humidity avg "
                        f"{row.humidity_avg_percent:.0f}%"
                    ),
                    (
                        f"wind avg "
                        f"{row.wind_speed_avg_mps:.1f}m/s"
                    ),
                ]
            )
        )

    return (
        current
        + "\n\n3-HOUR FORECAST\n"
        + "\n".join(forecast_lines)
        + "\n\nDAILY SUMMARY\n"
        + "\n".join(daily_lines)
    )


def _build_history_context(history):
    """
    Preserve all earlier exchanges in this report.

    Maximum history is tiny because SkyBrief allows
    only three questions total.
    """

    if not history:
        return "No previous conversation."

    lines = [
        "PREVIOUS CONVERSATION"
    ]

    for index, exchange in enumerate(
        history,
        start=1,
    ):
        lines.append(
            f"\nQuestion {index}: "
            f"{exchange['question']}"
        )

        lines.append(
            f"Answer {index}: "
            f"{exchange['answer']}"
        )

    return "\n".join(lines)


def _generate_answer(
    client,
    prompt,
):

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            max_output_tokens=2000,
            thinking_config=types.ThinkingConfig(
                thinking_level="low"
            ),
            automatic_function_calling={
                "disable": True
            },
            system_instruction=(
                QA_SYSTEM_INSTRUCTION
            ),
        ),
    )

    if not response.text:
        raise RuntimeError(
            f"{GEMINI_MODEL} returned "
            "an empty answer."
        )

    if response.candidates:

        finish_reason = str(
            response.candidates[
                0
            ].finish_reason
        ).upper()

        if "MAX_TOKENS" in finish_reason:

            raise RuntimeError(
                f"{GEMINI_MODEL} hit "
                "the output-token limit."
            )

    return response.text.strip()

def answer_weather_question(
    api_key,
    question,
    current_summary,
    forecast_df,
    daily_summary_df,
    history=None,
    question_number=1,
    questions_remaining_after=2,
):
    """
    Answer one weather question with conversational
    continuity and awareness of the 3-question limit.

    Each question gets:
    - Gemini 3.6 Flash
    - low thinking
    - 45 second request timeout
    - one retry
    """

    question = question.strip()

    if not question:
        raise ValueError(
            "Question cannot be empty."
        )

    weather_context = _compact_weather_context(
        current_summary=current_summary,
        forecast_df=forecast_df,
        daily_summary_df=daily_summary_df,
    )

    history_context = _build_history_context(
        history or []
    )

    final_question = (
        questions_remaining_after == 0
    )

    prompt = f"""
WEATHER DATA

{weather_context}


CHAT HISTORY

{history_context}


CURRENT TURN

This is question {question_number} of 3.
Questions remaining AFTER this answer:
{questions_remaining_after}

Final question: {final_question}


USER QUESTION

{question[:800]}


INSTRUCTIONS FOR THIS TURN

Continue naturally from the earlier conversation.

Answer everything requested in this question.

Do not offer something that you already supplied
in the current or previous answers.

If Final question is True:
- do not invite another question
- do not offer another future analysis
- close by acknowledging that 3/3 questions are complete
""".strip()

    client = create_gemini_client(
        api_key=api_key
    )

    answer = run_with_one_retry(
        operation=lambda: _generate_answer(
            client=client,
            prompt=prompt,
        ),
        operation_name=(
            f"Ask the Sky question "
            f"{question_number}"
        ),
    )

    return {
        "answer": answer,
        "model": GEMINI_MODEL,
        "used_fallback": False,
        "primary_error": None,
    }

