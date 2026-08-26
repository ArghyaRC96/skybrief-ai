# SkyBrief AI - Build Log

## 2026-08-26 - Gemini Runtime Hardening

### Goal

Reduce long AI processing times and align SkyBrief with
the runtime reliability pattern used across the portfolio.

### Changes

- retained Streamlit only as the UI layer
- confirmed src/skybrief has no Streamlit dependencies
- centralized Gemini configuration in gemini_runtime.py
- changed the active model to gemini-3.6-flash
- retained low thinking capability
- added a 45-second timeout per Gemini request
- configured one retry for the AI Brief
- configured one retry for every Ask the Sky question
- limited each operation to two total application attempts
- disabled additional Gemini SDK retry attempts
- removed the Gemini 3.7 to 3.6 fallback chain
- retained existing return fields for Streamlit compatibility
- updated README runtime documentation
- added project continuity documentation

### Runtime Flow

AI Brief:
request -> 45 second timeout -> one retry -> failure

Ask the Sky:
question -> 45 second timeout -> one retry -> failure

### Model

gemini-3.6-flash

### Deployment

Streamlit Community Cloud

https://skybrief-ai.streamlit.app/

### Repository

https://github.com/ArghyaRC96/skybrief-ai
