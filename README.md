# SkyBrief AI

SkyBrief AI is an AI-powered weather intelligence and group-planning application built with Streamlit, OpenWeather, Google Gemini, Plotly, Pandas, and Brevo.

It transforms numerical forecast data into interactive weather signals, grounded AI interpretation, contextual planning Q&A, and a shareable weather report for up to 20 recipients.

---

## Features

- Preset Indian cities plus manual latitude and longitude
- Current weather conditions
- Multi-day forecast aggregation
- Heat Pulse and Rain Pulse visualizations
- Gemini-powered weather interpretation
- Context-aware Ask the Sky Q&A
- Maximum 3 Q&A questions per generated forecast
- Multi-recipient transactional email delivery
- Up to 20 private recipients
- Brevo batch delivery using one API request
- Duplicate-send protection
- Streamlit secret management
- AWS and Terraform architecture retained from the original engineering challenge

---

## Application Flow

```text
City or Coordinates
        |
        v
OpenWeather API
        |
        v
Weather Processing
        |
        +-------------------+
        |                   |
        v                   v
Plotly Charts         Gemini AI Brief
        |                   |
        +---------+---------+
                  |
                  v
            Ask the Sky
        Contextual Weather Q&A
                  |
                  v
          Final SkyBrief Report
                  |
                  v
          Brevo Batch Email
                  |
                  v
            1-20 Recipients
```

---

## Core Components

### Weather Data

OpenWeather provides the numerical source of truth.

SkyBrief processes:

- Temperature
- Feels-like temperature
- Humidity
- Pressure
- Wind speed
- Cloudiness
- Rain probability
- Weather conditions

The forecast is also aggregated into daily summaries for easier interpretation.

### Weather Pulse

Plotly powers two primary forecast visualizations.

Heat Pulse:

- Air temperature
- Feels-like temperature
- Forecast high
- Forecast low
- Feels-like peak

Rain Pulse:

- Rain probability
- Humidity
- Peak rain probability
- Average humidity
- Dry-window count

### AI Brief

Google Gemini interprets structured OpenWeather data and produces:

- Overall Outlook
- Temperature Trend
- Rain and Humidity
- Wind Conditions
- Best Outdoor Window
- Things to Watch
- Practical Suggestions

Gemini interprets the supplied forecast data rather than generating weather measurements independently.

### Ask the Sky

Users can ask up to three contextual planning questions for each generated forecast.

Examples:

- Is tomorrow afternoon suitable for football?
- Why would that time be uncomfortable?
- Suggest a better outdoor window.
- Find the best six-hour daytime picnic window.

Conversation history is preserved across the three questions.

### Email Delivery

SkyBrief can send the final report to 1-20 recipients.

The email contains:

- Current conditions
- Multi-day forecast
- AI Brief
- Ask the Sky Q&A, when used

Brevo message versions keep recipient addresses private while allowing the application to submit the batch through one API request.

---

## Architecture

```text
                    Streamlit
                        |
                        v
                SkyBrief Python Core
                        |
        +---------------+---------------+
        |               |               |
        v               v               v
   OpenWeather        Gemini          Brevo
   Weather API        AI API          Email API
        |               |               |
        +---------------+---------------+
                        |
                        v
                Final SkyBrief Report
```

---

## Project Structure

```text
skybrief-ai/
|
|-- app.py
|-- requirements.txt
|-- README.md
|-- .gitignore
|
|-- .streamlit/
|   |-- config.toml
|   `-- secrets.toml.example
|
|-- src/
|   `-- skybrief/
|       |-- __init__.py
|       |-- cities.py
|       |-- weather.py
|       |-- charts.py
|       |-- ai_insights.py
|       |-- weather_qa.py
|       `-- email_service.py
|
|-- notebooks/
|   |-- 01_weather_analysis.ipynb
|   |-- 02_email_delivery.ipynb
|   `-- 03_weather_email_pipeline.ipynb
|
|-- docs/
|-- lambda_src/
`-- terraform/
```

---

## Technology Stack

| Layer | Technology |
|---|---|
| User interface | Streamlit |
| Programming language | Python |
| Weather data | OpenWeather API |
| AI interpretation | Google Gemini |
| Data processing | Pandas |
| Visualization | Plotly |
| Email delivery | Brevo Transactional Email API |
| HTTP client | Requests |
| Infrastructure design | AWS |
| Infrastructure as Code | Terraform |
| Portfolio deployment | Streamlit Community Cloud |

---

## AI Design

SkyBrief follows a grounded generation pattern.

```text
OpenWeather numerical data
          |
          v
Structured weather context
          |
          v
Google Gemini
          |
          v
Human-readable interpretation
```

The language model is used for interpretation and planning assistance. Numerical weather measurements remain grounded in OpenWeather data.

Current model configuration:

```text
Primary model  : gemini-3.7-flash
Fallback model : gemini-3.6-flash
Thinking level : low
```

---

## Local Setup

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd skybrief-ai
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Configure secrets

Create:

```text
.streamlit/secrets.toml
```

Use `.streamlit/secrets.toml.example` as the template.

Required values:

```toml
OPENWEATHER_API_KEY = "your_openweather_api_key"
GEMINI_API_KEY = "your_gemini_api_key"

BREVO_API_KEY = "your_brevo_api_key"
SENDER_EMAIL = "your_verified_brevo_sender_email"
SENDER_NAME = "SkyBrief AI"
```

Never commit the real `secrets.toml` file.

### 5. Run the application

```powershell
python -m streamlit run ".\app.py"
```

---

## Tested Dependency Versions

```text
streamlit==1.62.0
requests==2.34.2
pandas==3.0.5
plotly==6.9.0
google-genai==2.19.0
```

---

## Security

Sensitive credentials are stored through Streamlit Secrets and excluded from Git.

The repository ignores:

- `.streamlit/secrets.toml`
- `.env` files
- virtual environments
- private keys
- Terraform state
- Terraform variable files
- Python caches

Brevo API access can additionally use authorized-IP restrictions.

---

## Current Limitations

- Forecast resolution depends on the OpenWeather endpoint.
- Forecast data is available at discrete time intervals rather than minute-level resolution.
- Weather recommendations are planning guidance, not safety guarantees.
- Ask the Sky is limited to three questions per generated forecast.
- Email delivery depends on Brevo sender verification and API configuration.
- Interactive Plotly charts are not embedded in email because email clients do not reliably support JavaScript visualizations.

---

## Future Improvements

- Scheduled automatic SkyBrief delivery
- Geocoding and broader location search
- Severe-weather alerts
- Calendar-aware activity planning
- Saved locations
- User accounts
- Multi-city comparison
- Static chart images inside emails
- Additional weather providers

---

## Project Background

SkyBrief AI evolved from a weather forecasting and email automation engineering challenge into a complete portfolio application.

The original project focused on weather API integration, analysis, email automation, serverless architecture, and Terraform.

SkyBrief extends that foundation with:

- A Streamlit product interface
- Reusable Python modules
- Grounded Gemini interpretation
- Contextual weather Q&A
- Interactive forecast visualization
- Multi-recipient batch email delivery
- Deployment-ready secret management

---

## Author

Arghya Roy Chowdhury

AI and Data Science portfolio project.

---

## Disclaimer

SkyBrief provides forecast interpretation and planning assistance based on third-party weather data. It should not be used as the sole source for emergency, aviation, marine, or other safety-critical decisions.
