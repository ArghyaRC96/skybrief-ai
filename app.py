import pandas as pd
import time

import streamlit as st

from src.skybrief.ai_insights import generate_weather_insights
from src.skybrief.weather_qa import answer_weather_question
from src.skybrief.charts import (
    create_rain_humidity_chart,
    create_temperature_chart,
)
from src.skybrief.cities import CITY_OPTIONS, INDIAN_CITIES
from src.skybrief.weather import get_weather_report_data
from src.skybrief.email_service import (
    is_valid_email,
    send_skybrief_email,
)


# ------------------------------------------------------------
# Page configuration
# ------------------------------------------------------------

st.set_page_config(
    page_title="SkyBrief AI",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ------------------------------------------------------------
# Premium SkyBrief visual system
# ------------------------------------------------------------

st.markdown(
    """
    <style>

    .stApp {
        background:
            radial-gradient(
                circle at 15% 0%,
                rgba(34, 211, 238, 0.10),
                transparent 28%
            ),
            radial-gradient(
                circle at 90% 20%,
                rgba(167, 139, 250, 0.10),
                transparent 30%
            ),
            linear-gradient(
                145deg,
                #050816 0%,
                #09111F 45%,
                #0B1220 100%
            );
    }

    [data-testid="stHeader"] {
        background: rgba(0,0,0,0);
    }

    .block-container {
        max-width: 1220px;
        padding-top: 2.2rem;
        padding-bottom: 5rem;
    }

    h1 {
        letter-spacing: -1.4px;
    }

    h2, h3 {
        letter-spacing: -0.5px;
    }

    div[data-testid="stMetric"] {
        background:
            linear-gradient(
                135deg,
                rgba(30, 41, 59, 0.72),
                rgba(15, 23, 42, 0.52)
            );

        border:
            1px solid rgba(148,163,184,0.12);

        border-radius: 18px;

        padding: 16px;

        box-shadow:
            0 10px 35px rgba(0,0,0,0.16);

        backdrop-filter: blur(15px);
    }

    div[data-testid="stMetricValue"] {
        font-weight: 700;
    }

    div[data-testid="stDataFrame"] {
        border-radius: 16px;
        overflow: hidden;

        border:
            1px solid rgba(148,163,184,0.10);
    }

    .stButton > button,
    [data-testid="stFormSubmitButton"] > button {
        border: 0;

        border-radius: 12px;

        background:
            linear-gradient(
                90deg,
                #0891B2,
                #7C3AED
            );

        color: white;

        font-weight: 650;

        box-shadow:
            0 8px 28px rgba(124,58,237,0.18);
    }

    .stButton > button:hover,
    [data-testid="stFormSubmitButton"] > button:hover {
        transform: translateY(-1px);
        border: 0;
    }

    div[data-testid="stMetric"] {
        min-height: 92px;
    }

    div[data-testid="stMetricLabel"] {
        color: #64748B;
        letter-spacing: 0.9px;
        font-size: 11px;
        font-weight: 700;
    }

    div[data-testid="stMetricValue"] {
        color: #F8FAFC;
        letter-spacing: -0.8px;
    }

    div[data-testid="stPlotlyChart"] {
        background:
            linear-gradient(
                145deg,
                rgba(15,23,42,0.42),
                rgba(8,15,32,0.20)
            );

        border:
            1px solid rgba(148,163,184,0.09);

        border-radius: 18px;

        padding:
            8px 12px 2px 12px;

        box-shadow:
            0 18px 48px rgba(0,0,0,0.12);
    }


    </style>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------------
# Secrets
# ------------------------------------------------------------

try:
    OPENWEATHER_API_KEY = st.secrets[
        "OPENWEATHER_API_KEY"
    ]

    GEMINI_API_KEY = st.secrets[
        "GEMINI_API_KEY"
    ]

    BREVO_API_KEY = st.secrets[
        "BREVO_API_KEY"
    ]

    SENDER_EMAIL = st.secrets[
        "SENDER_EMAIL"
    ]

    SENDER_NAME = st.secrets.get(
        "SENDER_NAME",
        "SkyBrief AI",
    )

except KeyError as error:
    st.error(
        f"Missing required Streamlit secret: {error}"
    )
    st.stop()


# ------------------------------------------------------------
# Cached OpenWeather request
#
# TTL = Time To Live.
# Weather data stays cached for 600 seconds / 10 minutes.
# ------------------------------------------------------------

@st.cache_data(
    ttl=600,
    show_spinner=False,
)
def load_weather(
    latitude,
    longitude,
    location_name,
    _api_key,
):
    return get_weather_report_data(
        latitude=latitude,
        longitude=longitude,
        location_name=location_name,
        api_key=_api_key,
    )


# ------------------------------------------------------------
# Hero
# ------------------------------------------------------------

st.markdown(
    """
    <div class="skybrief-hero">
        <h1>☁️ SkyBrief AI</h1>
        <div class="skybrief-subtitle">
            Weather intelligence, interactive forecasting,
            and grounded AI-powered insights.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()


# ------------------------------------------------------------
# Location selection
# ------------------------------------------------------------

st.subheader("📍 Choose your location")

selected_city = st.selectbox(
    "City",
    CITY_OPTIONS,
    index=CITY_OPTIONS.index("Bengaluru"),
)


if selected_city != "Other / Manual":

    location_name = selected_city

    latitude, longitude = (
        INDIAN_CITIES[selected_city]
    )

    coord_col1, coord_col2 = st.columns(2)

    with coord_col1:
        st.number_input(
            "Latitude",
            value=float(latitude),
            format="%.4f",
            disabled=True,
            key=f"preset_lat_{selected_city}",
        )

    with coord_col2:
        st.number_input(
            "Longitude",
            value=float(longitude),
            format="%.4f",
            disabled=True,
            key=f"preset_lon_{selected_city}",
        )

else:

    location_name = st.text_input(
        "City / Location Name",
        placeholder="Example: Mysuru",
    )

    coord_col1, coord_col2 = st.columns(2)

    with coord_col1:
        latitude = st.number_input(
            "Latitude",
            min_value=-90.0,
            max_value=90.0,
            value=12.2958,
            format="%.4f",
            key="manual_latitude",
        )

    with coord_col2:
        longitude = st.number_input(
            "Longitude",
            min_value=-180.0,
            max_value=180.0,
            value=76.6394,
            format="%.4f",
            key="manual_longitude",
        )



st.subheader(
    "📨 Delivery"
)

st.caption(
    "Send the final SkyBrief to up to 20 people."
)


# ------------------------------------------------------------
# Dynamic recipient inputs
# ------------------------------------------------------------

if "recipient_count" not in st.session_state:
    st.session_state[
        "recipient_count"
    ] = 1


recipient_count = st.session_state[
    "recipient_count"
]


for index in range(
    recipient_count
):

    st.text_input(
        f"Receiver {index + 1}",
        placeholder="name@example.com",
        key=f"receiver_email_{index}",
    )


add_col, remove_col, count_col = (
    st.columns(
        [1, 1, 2]
    )
)


with add_col:

    add_recipient = st.button(
        "＋ Add email",
        disabled=(
            recipient_count >= 20
        ),
        key="add_receiver_email",
    )


with remove_col:

    remove_recipient = st.button(
        "− Remove last",
        disabled=(
            recipient_count <= 1
        ),
        key="remove_receiver_email",
    )


with count_col:

    st.caption(
        f"{recipient_count} / 20 recipient slots"
    )


if add_recipient:

    st.session_state[
        "recipient_count"
    ] += 1

    st.rerun()


if remove_recipient:

    last_index = (
        st.session_state[
            "recipient_count"
        ] - 1
    )

    st.session_state.pop(
        f"receiver_email_{last_index}",
        None,
    )

    st.session_state[
        "recipient_count"
    ] -= 1

    st.rerun()


receiver_emails = []

for index in range(
    st.session_state[
        "recipient_count"
    ]
):

    email = st.session_state.get(
        f"receiver_email_{index}",
        "",
    ).strip()

    if email:
        receiver_emails.append(
            email
        )


# Deduplicate while preserving order.

receiver_emails = list(
    dict.fromkeys(
        receiver_emails
    )
)


generate_report = st.button(
    "✨ Generate SkyBrief",
    type="primary",
    width="stretch",
)


# ------------------------------------------------------------
# Generate report
# ------------------------------------------------------------

if generate_report:

    if not location_name.strip():
        st.warning(
            "Please enter a location name."
        )
        st.stop()

    if not receiver_emails:

        st.warning(
            "Add at least one receiver email."
        )

        st.stop()


    if len(receiver_emails) > 20:

        st.warning(
            "SkyBrief supports up to 20 recipients."
        )

        st.stop()


    invalid_emails = [
        email
        for email in receiver_emails
        if not is_valid_email(email)
    ]


    if invalid_emails:

        st.warning(
            "Check these email addresses: "
            + ", ".join(
                invalid_emails
            )
        )

        st.stop()

    try:

        with st.spinner(
            "Reading the skies..."
        ):
            weather_result = load_weather(
                latitude=float(latitude),
                longitude=float(longitude),
                location_name=location_name.strip(),
                _api_key=OPENWEATHER_API_KEY,
            )

        with st.spinner(
            "Gemini is preparing your SkyBrief..."
        ):
            ai_result = generate_weather_insights(
                api_key=GEMINI_API_KEY,
                current_summary=weather_result[
                    "current_summary"
                ],
                forecast_df=weather_result[
                    "forecast_df"
                ],
                daily_summary_df=weather_result[
                    "daily_summary_df"
                ],
            )

        st.session_state[
            "skybrief_report"
        ] = {
            "location_name": location_name.strip(),
            "latitude": float(latitude),
            "longitude": float(longitude),
            "weather": weather_result,
            "ai": ai_result,
            "receiver_emails": receiver_emails.copy(),
        }

        st.session_state[
            "weather_qa_history"
        ] = []

    except Exception as error:

        st.error(
            "SkyBrief could not generate the report."
        )

        with st.expander(
            "Technical details"
        ):
            st.code(str(error))

        st.stop()


# ------------------------------------------------------------
# Render existing report
# ------------------------------------------------------------

if "skybrief_report" in st.session_state:

    report = st.session_state[
        "skybrief_report"
    ]

    weather = report["weather"]

    current = weather[
        "current_summary"
    ]

    forecast_df = weather[
        "forecast_df"
    ]

    daily_df = weather[
        "daily_summary_df"
    ].copy()

    ai_result = report["ai"]

    location = report[
        "location_name"
    ]


    st.divider()

    st.header(
        f"🌤️ Weather for {location}"
    )


    # --------------------------------------------------------
    # Current weather cards
    # --------------------------------------------------------

    metric1, metric2, metric3, metric4, metric5 = (
        st.columns(5)
    )

    metric1.metric(
        "Temperature",
        f"{current['temperature_celsius']:.1f} °C",
    )

    metric2.metric(
        "Feels Like",
        f"{current['feels_like_celsius']:.1f} °C",
    )

    metric3.metric(
        "Humidity",
        f"{current['humidity_percent']:.0f}%",
    )

    metric4.metric(
        "Wind",
        f"{current['wind_speed_mps']:.1f} m/s",
    )

    metric5.metric(
        "Cloud Cover",
        f"{current['cloudiness_percent']:.0f}%",
    )


    st.caption(
        "Current condition: "
        + current[
            "weather_description"
        ].title()
    )


    # --------------------------------------------------------
    # Five-day outlook table
    # --------------------------------------------------------

    st.subheader(
        "📅 5-Day Pulse"
    )

    display_daily = (
        daily_df
        .head(5)
        .copy()
    )

    display_daily["date"] = pd.to_datetime(
        display_daily["date"]
    ).dt.strftime(
        "%a, %d %b"
    )

    display_daily = display_daily.rename(
        columns={
            "date": "Date",
            "temp_min_celsius": "Min °C",
            "temp_max_celsius": "Max °C",
            "temp_avg_celsius": "Avg °C",
            "humidity_avg_percent": "Humidity %",
            "wind_speed_avg_mps": "Wind m/s",
            "rain_probability_max": "Rain %",
            "cloudiness_avg_percent": "Cloud %",
        }
    )

    numeric_columns = [
        "Min °C",
        "Max °C",
        "Avg °C",
        "Humidity %",
        "Wind m/s",
        "Rain %",
        "Cloud %",
    ]

    display_daily[
        numeric_columns
    ] = display_daily[
        numeric_columns
    ].round(1)

    st.dataframe(
        display_daily,
        width="stretch",
        hide_index=True,
    )



    # --------------------------------------------------------
    # Weather Pulse
    # --------------------------------------------------------

    st.caption(
        "FORECAST SIGNALS"
    )

    st.header(
        "Weather Pulse"
    )


    # --------------------------------------------------------
    # Heat Pulse
    # --------------------------------------------------------

    temp_high = (
        forecast_df[
            "temperature_celsius"
        ].max()
    )

    temp_low = (
        forecast_df[
            "temperature_celsius"
        ].min()
    )

    feels_peak = (
        forecast_df[
            "feels_like_celsius"
        ].max()
    )


    st.caption(
        "TEMPERATURE"
    )

    st.subheader(
        "🌡️ Heat Pulse"
    )


    heat_1, heat_2, heat_3 = (
        st.columns(3)
    )


    heat_1.metric(
        "HIGH",
        f"{temp_high:.1f}°",
    )

    heat_2.metric(
        "LOW",
        f"{temp_low:.1f}°",
    )

    heat_3.metric(
        "FEELS PEAK",
        f"{feels_peak:.1f}°",
    )


    temperature_fig = (
        create_temperature_chart(
            forecast_df=forecast_df,
            location_name=location,
        )
    )


    st.plotly_chart(
        temperature_fig,

        width="stretch",

        config={
            "displaylogo": False,
            "displayModeBar": False,
            "scrollZoom": False,
        },
    )


    # --------------------------------------------------------
    # Rain Pulse
    # --------------------------------------------------------

    peak_rain = (
        forecast_df[
            "rain_probability_percent"
        ].max()
    )

    avg_humidity = (
        forecast_df[
            "humidity_percent"
        ].mean()
    )

    dry_windows = int(
        (
            forecast_df[
                "rain_probability_percent"
            ] <= 10
        ).sum()
    )


    st.caption(
        "PRECIPITATION"
    )

    st.subheader(
        "🌧️ Rain Pulse"
    )


    rain_1, rain_2, rain_3 = (
        st.columns(3)
    )


    rain_1.metric(
        "PEAK RAIN",
        f"{peak_rain:.0f}%",
    )

    rain_2.metric(
        "AVG HUMIDITY",
        f"{avg_humidity:.0f}%",
    )

    rain_3.metric(
        "DRY WINDOWS",
        dry_windows,
    )


    rain_humidity_fig = (
        create_rain_humidity_chart(
            forecast_df=forecast_df,
            location_name=location,
        )
    )


    st.plotly_chart(
        rain_humidity_fig,

        width="stretch",

        config={
            "displaylogo": False,
            "displayModeBar": False,
            "scrollZoom": False,
        },
    )


    # --------------------------------------------------------
    # Gemini SkyBrief
    # --------------------------------------------------------

    st.subheader(
        "⚡ AI Brief"
    )

    st.markdown(
        ai_result["text"]
    )

    st.caption(
        f"Generated with {ai_result['model']} · "
        "OpenWeather forecast data is the numerical "
        "source of truth."
    )



    # --------------------------------------------------------
    # Ask the Sky - Weather Q&A
    # --------------------------------------------------------

    st.divider()

    st.subheader(
        "💬 Ask the Sky"
    )

    st.caption(
        "Quick weather planning · up to 3 questions."
    )


    if (
        "weather_qa_history"
        not in st.session_state
    ):

        st.session_state[
            "weather_qa_history"
        ] = []


    qa_history = st.session_state[
        "weather_qa_history"
    ]


    # --------------------------------------------------------
    # Display existing Q&A
    # --------------------------------------------------------

    for exchange in qa_history:

        with st.chat_message(
            "user"
        ):
            st.markdown(
                exchange["question"]
            )


        with st.chat_message(
            "assistant",
            avatar="☁️",
        ):
            st.markdown(
                exchange["answer"]
            )


    questions_left = (
        3 - len(qa_history)
    )


    # --------------------------------------------------------
    # New question
    # --------------------------------------------------------

    if questions_left > 0:

        with st.form(
            "skybrief_weather_qa",
            clear_on_submit=True,
        ):

            question = st.text_input(
                "Ask about this forecast",
                placeholder=(
                    "Picnic on 28 Aug, "
                    "10 AM–3 PM — good idea?"
                ),
                label_visibility="collapsed",
            )


            ask_button = (
                st.form_submit_button(
                    (
                        f"Ask SkyBrief · "
                        f"{questions_left} left"
                    ),
                    type="primary",
                    width="stretch",
                )
            )


        if ask_button:

            if not question.strip():

                st.warning(
                    "Ask me something about "
                    "this forecast."
                )

            else:

                try:

                    with st.spinner(
                        "Reading the weather window..."
                    ):

                        question_number = (
                            len(qa_history) + 1
                        )

                        questions_remaining_after = (
                            3 - question_number
                        )


                        qa_result = (
                            answer_weather_question(
                                api_key=GEMINI_API_KEY,

                                question=question,

                                current_summary=current,

                                forecast_df=forecast_df,

                                daily_summary_df=daily_df,

                                history=qa_history,

                                question_number=(
                                    question_number
                                ),

                                questions_remaining_after=(
                                    questions_remaining_after
                                ),
                            )
                        )


                    qa_history.append(
                        {
                            "question": question.strip(),

                            "answer": (
                                qa_result["answer"]
                            ),

                            "model": (
                                qa_result["model"]
                            ),
                        }
                    )


                    st.session_state[
                        "weather_qa_history"
                    ] = qa_history


                    st.rerun()


                except Exception as error:

                    st.error(
                        "Ask the Sky couldn't answer "
                        "that one."
                    )

                    with st.expander(
                        "Technical details"
                    ):

                        st.code(
                            str(error)
                        )


    else:

        st.info(
            "3/3 questions used. "
            "Your full Q&A will be included "
            "in the final email."
        )


    # --------------------------------------------------------
    # Final SkyBrief email delivery
    # --------------------------------------------------------

    st.divider()

    st.subheader(
        "\U0001F4E8 Send the Full SkyBrief"
    )


    final_receivers = report[
        "receiver_emails"
    ]


    qa_history_for_email = (
        st.session_state.get(
            "weather_qa_history",
            [],
        )
    )


    question_count = len(
        qa_history_for_email
    )


    # --------------------------------------------------------
    # Show success message after Streamlit rerun
    # --------------------------------------------------------

    email_success_message = (
        st.session_state.pop(
            "skybrief_email_success_message",
            None,
        )
    )


    if email_success_message:

        st.success(
            email_success_message
        )


    st.caption(
        f"Ready for {len(final_receivers)} "
        f"{'person' if len(final_receivers) == 1 else 'people'} "
        f"\u00B7 {question_count} Q&A "
        f"{'exchange' if question_count == 1 else 'exchanges'} "
        "included."
    )


    # --------------------------------------------------------
    # Lightweight per-session email protection
    # --------------------------------------------------------

    EMAIL_SEND_LIMIT = 3
    EMAIL_SEND_COOLDOWN_SECONDS = 60


    email_send_count = (
        st.session_state.get(
            "skybrief_email_send_count",
            0,
        )
    )


    last_email_send_at = (
        st.session_state.get(
            "skybrief_email_last_send_at",
            0.0,
        )
    )


    seconds_since_last_send = (
        time.time()
        - last_email_send_at
    )


    cooldown_remaining = max(
        0,
        int(
            EMAIL_SEND_COOLDOWN_SECONDS
            - seconds_since_last_send
        ),
    )


    email_limit_reached = (
        email_send_count
        >= EMAIL_SEND_LIMIT
    )


    email_cooldown_active = (
        cooldown_remaining > 0
    )


    st.caption(
        f"Email sends this session: "
        f"{email_send_count}/{EMAIL_SEND_LIMIT}"
    )


    if email_limit_reached:

        st.warning(
            "This session has reached the "
            "email-send limit."
        )


    elif email_cooldown_active:

        st.info(
            f"Email cooldown active. "
            f"Try again in about "
            f"{cooldown_remaining} seconds."
        )


    send_final_email = st.button(
        "Send Final SkyBrief",
        type="primary",
        width="stretch",
        key="send_final_skybrief",
        disabled=email_limit_reached,
    )


    if send_final_email:

        # ----------------------------------------------------
        # Do not call Brevo while cooldown is active.
        # ----------------------------------------------------

        if email_cooldown_active:

            st.warning(
                f"Please wait about "
                f"{cooldown_remaining} seconds "
                f"before sending another SkyBrief."
            )


        else:

            try:

                with st.spinner(
                    "Packaging your SkyBrief..."
                ):

                    send_result = (
                        send_skybrief_email(
                            api_key=BREVO_API_KEY,

                            sender_email=(
                                SENDER_EMAIL
                            ),

                            sender_name=(
                                SENDER_NAME
                            ),

                            receiver_emails=(
                                final_receivers
                            ),

                            location_name=(
                                location
                            ),

                            current_summary=(
                                current
                            ),

                            daily_summary_df=(
                                daily_df
                            ),

                            ai_text=(
                                ai_result["text"]
                            ),

                            qa_history=(
                                qa_history_for_email
                            ),
                        )
                    )


                # --------------------------------------------
                # Count only successful Brevo submissions.
                # --------------------------------------------

                st.session_state[
                    "skybrief_email_send_count"
                ] = (
                    email_send_count
                    + 1
                )


                st.session_state[
                    "skybrief_email_last_send_at"
                ] = time.time()


                sent_count = send_result[
                    "recipient_count"
                ]


                st.session_state[
                    "skybrief_email_success_message"
                ] = (
                    "\u2601\ufe0f SkyBrief accepted for "
                    f"delivery to {sent_count} "
                    f"{'person' if sent_count == 1 else 'people'}."
                )


                # --------------------------------------------
                # Rerun so 0/3 immediately becomes 1/3.
                # --------------------------------------------

                st.rerun()


            except Exception as error:

                st.error(
                    "SkyBrief couldn't send the email."
                )

                with st.expander(
                    "Technical details"
                ):

                    st.code(
                        str(error)
                    )
