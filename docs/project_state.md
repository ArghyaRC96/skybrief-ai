# SkyBrief AI - Project State

Updated: 2026-08-26

## Status

Production-ready portfolio application.

Live App:
https://skybrief-ai.streamlit.app/

GitHub:
https://github.com/ArghyaRC96/skybrief-ai

## Current Architecture

SkyBrief separates the Streamlit interface from the
reusable Python application modules.

app.py
- Streamlit user interface
- session state
- report rendering
- user interactions

src/skybrief/
- weather retrieval and transformation
- chart generation
- AI insight generation
- conversational weather Q&A
- email generation and delivery
- shared Gemini runtime

## Gemini Runtime

Model:
gemini-3.6-flash

Thinking level:
low

Request timeout:
45 seconds per attempt

Retry policy:
- first attempt
- one retry
- maximum two total attempts

The Google Gen AI SDK is configured for one internal
attempt so SkyBrief owns the retry count explicitly.

There is no longer a Gemini 3.7 to Gemini 3.6 model
fallback chain.

## Streamlit Independence

Core modules under src/skybrief do not import Streamlit.

The AI runtime can therefore be imported and tested
directly from Python without launching the Streamlit UI.

## Current Product Capabilities

- OpenWeather current conditions
- 5-day / 3-hour forecast processing
- daily weather summaries
- interactive Plotly weather visualizations
- Gemini-grounded AI Brief
- Ask the Sky contextual weather Q&A
- up to 3 questions per generated report
- multi-recipient Brevo HTML email delivery
- session-level email send protection
- Streamlit Community Cloud deployment

## Source of Truth

OpenWeather data remains the factual weather source.

Gemini interprets the supplied structured weather data
but does not replace the weather provider.

## Current State

Runtime hardening completed on 2026-08-26.

The next development session should begin from this
document and docs/build_log.md.
