import html
import re
import time
import uuid

import pandas as pd
import requests


BREVO_EMAIL_URL = "https://api.brevo.com/v3/smtp/email"


def is_valid_email(email):
    """
    Lightweight receiver-email validation.
    """

    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    return bool(
        re.match(
            pattern,
            email.strip(),
        )
    )


def _inline_markdown(text):
    """
    Convert the small subset of Markdown used by
    Gemini into email-friendly HTML.
    """

    escaped = html.escape(
        str(text)
    )

    escaped = re.sub(
        r"\*\*(.+?)\*\*",
        r"<strong>\1</strong>",
        escaped,
    )

    return escaped


def _render_ai_brief(text):
    """
    Convert structured Gemini SkyBrief Markdown into
    styled email HTML.
    """

    parts = []

    in_list = False

    for raw_line in text.splitlines():

        line = raw_line.strip()

        if not line:
            continue


        if line.startswith("## "):

            if in_list:
                parts.append("</ul>")
                in_list = False

            heading = _inline_markdown(
                line[3:]
            )

            parts.append(
                f"""
                <h3 style="
                    margin:24px 0 8px 0;
                    color:#F8FAFC;
                    font-size:17px;
                    line-height:1.3;
                ">
                    {heading}
                </h3>
                """
            )


        elif line.startswith("- "):

            if not in_list:

                parts.append(
                    """
                    <ul style="
                        margin:8px 0 12px 0;
                        padding-left:20px;
                        color:#CBD5E1;
                    ">
                    """
                )

                in_list = True


            item = _inline_markdown(
                line[2:]
            )

            parts.append(
                f"""
                <li style="
                    margin:6px 0;
                    line-height:1.55;
                ">
                    {item}
                </li>
                """
            )


        else:

            if in_list:
                parts.append("</ul>")
                in_list = False

            paragraph = _inline_markdown(
                line
            )

            parts.append(
                f"""
                <p style="
                    margin:7px 0 11px 0;
                    color:#CBD5E1;
                    line-height:1.65;
                ">
                    {paragraph}
                </p>
                """
            )


    if in_list:
        parts.append("</ul>")


    return "".join(parts)


def _build_forecast_rows(
    daily_summary_df,
):
    """
    Create five compact forecast rows.
    """

    daily = (
        daily_summary_df
        .head(5)
        .copy()
    )

    daily["date"] = pd.to_datetime(
        daily["date"]
    )


    rows = []


    for row in daily.itertuples():

        date_text = row.date.strftime(
            "%a, %d %b"
        )


        rows.append(
            f"""
            <tr>
                <td style="
                    padding:14px 8px;
                    border-bottom:1px solid #1E293B;
                    color:#E2E8F0;
                ">
                    <strong>{date_text}</strong>
                </td>

                <td style="
                    padding:14px 8px;
                    border-bottom:1px solid #1E293B;
                    color:#CBD5E1;
                ">
                    {row.temp_min_celsius:.1f}° –
                    {row.temp_max_celsius:.1f}°
                </td>

                <td style="
                    padding:14px 8px;
                    border-bottom:1px solid #1E293B;
                    color:#67E8F9;
                ">
                    {row.rain_probability_max:.0f}%
                </td>

                <td style="
                    padding:14px 8px;
                    border-bottom:1px solid #1E293B;
                    color:#CBD5E1;
                ">
                    {row.humidity_avg_percent:.0f}%
                </td>
            </tr>
            """
        )


    return "".join(rows)


def _build_qa_html(
    qa_history,
):
    """
    Build optional Q&A section.

    Works with:
    - zero questions
    - one question
    - two questions
    - three questions
    """

    if not qa_history:

        return """
        <div style="
            padding:18px;
            border-radius:14px;
            background:#111827;
            border:1px solid #1E293B;
            color:#94A3B8;
        ">
            No follow-up questions were asked
            for this forecast.
        </div>
        """


    blocks = []


    for index, exchange in enumerate(
        qa_history,
        start=1,
    ):

        question = _inline_markdown(
            exchange["question"]
        )

        answer = _inline_markdown(
            exchange["answer"]
        )


        blocks.append(
            f"""
            <div style="
                margin:0 0 16px 0;
                padding:18px;
                border-radius:16px;
                background:#111827;
                border:1px solid #1E293B;
            ">

                <div style="
                    font-size:11px;
                    letter-spacing:1.2px;
                    color:#22D3EE;
                    font-weight:700;
                    margin-bottom:7px;
                ">
                    QUESTION {index}
                </div>

                <div style="
                    color:#F8FAFC;
                    font-weight:600;
                    line-height:1.5;
                    margin-bottom:12px;
                ">
                    {question}
                </div>

                <div style="
                    font-size:11px;
                    letter-spacing:1.2px;
                    color:#A78BFA;
                    font-weight:700;
                    margin-bottom:7px;
                ">
                    SKYBRIEF
                </div>

                <div style="
                    color:#CBD5E1;
                    line-height:1.6;
                ">
                    {answer}
                </div>

            </div>
            """
        )


    return "".join(blocks)


def build_skybrief_email(
    location_name,
    current_summary,
    daily_summary_df,
    ai_text,
    qa_history,
):
    """
    Build the final HTML email snapshot.
    """

    forecast_rows = _build_forecast_rows(
        daily_summary_df
    )

    ai_html = _render_ai_brief(
        ai_text
    )

    qa_html = _build_qa_html(
        qa_history
    )


    return f"""
    <!DOCTYPE html>

    <html>

    <body style="
        margin:0;
        padding:0;
        background:#050816;
        font-family:Arial, Helvetica, sans-serif;
    ">

    <table
        width="100%"
        cellspacing="0"
        cellpadding="0"
        style="background:#050816;"
    >

    <tr>

    <td align="center" style="padding:32px 14px;">

    <table
        width="100%"
        cellspacing="0"
        cellpadding="0"
        style="
            max-width:720px;
            background:#0B1220;
            border:1px solid #1E293B;
            border-radius:22px;
            overflow:hidden;
        "
    >


    <tr>
    <td style="
        padding:34px 34px 28px 34px;
        background:
            linear-gradient(
                135deg,
                #0E7490,
                #312E81
            );
    ">

        <div style="
            color:#BAE6FD;
            font-size:12px;
            letter-spacing:2px;
            font-weight:700;
        ">
            SKYBRIEF AI
        </div>

        <div style="
            margin-top:8px;
            color:#FFFFFF;
            font-size:32px;
            font-weight:800;
        ">
            {html.escape(location_name)}
        </div>

        <div style="
            margin-top:7px;
            color:#E0F2FE;
            font-size:14px;
        ">
            Your weather pulse, decoded.
        </div>

    </td>
    </tr>


    <tr>
    <td style="padding:30px 34px;">


        <div style="
            color:#64748B;
            font-size:11px;
            letter-spacing:1.5px;
            font-weight:700;
            margin-bottom:14px;
        ">
            RIGHT NOW
        </div>


        <table
            width="100%"
            cellspacing="0"
            cellpadding="0"
        >

        <tr>

        <td style="
            width:33%;
            padding-right:10px;
        ">
            <div style="
                color:#FFFFFF;
                font-size:25px;
                font-weight:700;
            ">
                {current_summary['temperature_celsius']:.1f}°C
            </div>

            <div style="
                color:#64748B;
                font-size:12px;
            ">
                Temperature
            </div>
        </td>


        <td style="
            width:33%;
            padding-right:10px;
        ">
            <div style="
                color:#FFFFFF;
                font-size:25px;
                font-weight:700;
            ">
                {current_summary['humidity_percent']:.0f}%
            </div>

            <div style="
                color:#64748B;
                font-size:12px;
            ">
                Humidity
            </div>
        </td>


        <td style="width:33%;">

            <div style="
                color:#FFFFFF;
                font-size:25px;
                font-weight:700;
            ">
                {current_summary['wind_speed_mps']:.1f}
            </div>

            <div style="
                color:#64748B;
                font-size:12px;
            ">
                Wind m/s
            </div>

        </td>

        </tr>

        </table>


        <div style="
            margin-top:20px;
            color:#CBD5E1;
            font-size:15px;
        ">
            {html.escape(
                current_summary[
                    'weather_description'
                ].title()
            )}
        </div>


        <div style="
            height:1px;
            background:#1E293B;
            margin:30px 0;
        "></div>


        <div style="
            color:#F8FAFC;
            font-size:20px;
            font-weight:750;
            margin-bottom:16px;
        ">
            📅 5-Day Pulse
        </div>


        <table
            width="100%"
            cellspacing="0"
            cellpadding="0"
            style="
                border-collapse:collapse;
                font-size:13px;
            "
        >

            <tr style="color:#64748B;">

                <td style="padding:8px;">
                    DAY
                </td>

                <td style="padding:8px;">
                    TEMP
                </td>

                <td style="padding:8px;">
                    RAIN
                </td>

                <td style="padding:8px;">
                    HUMIDITY
                </td>

            </tr>

            {forecast_rows}

        </table>


        <div style="
            height:1px;
            background:#1E293B;
            margin:32px 0;
        "></div>


        <div style="
            color:#F8FAFC;
            font-size:20px;
            font-weight:750;
            margin-bottom:12px;
        ">
            &#9889; AI Brief
        </div>


        {ai_html}


        <div style="
            height:1px;
            background:#1E293B;
            margin:32px 0;
        "></div>


        <div style="
            color:#F8FAFC;
            font-size:20px;
            font-weight:750;
            margin-bottom:16px;
        ">
            💬 Ask the Sky
        </div>


        {qa_html}


        <div style="
            height:1px;
            background:#1E293B;
            margin:32px 0 22px 0;
        "></div>


        <div style="
            color:#64748B;
            font-size:11px;
            line-height:1.6;
        ">
            Numerical weather data provided by OpenWeather.
            AI interpretation powered by Gemini.
            Forecasts can change — check live conditions
            before weather-sensitive plans.
        </div>

    </td>
    </tr>


    </table>

    </td>
    </tr>

    </table>

    </body>
    </html>
    """


def _build_idempotency_key(
    sender_email,
    location_name,
    current_summary,
    receiver_emails,
    qa_history,
):
    """
    Create a stable ID for one exact SkyBrief snapshot.

    If the same sender + report + recipients + Q&A are
    submitted again immediately, Brevo can identify it
    as the same batch.
    """

    qa_signature = "|".join(
        (
            exchange.get(
                "question",
                "",
            )
            + "::"
            + exchange.get(
                "answer",
                "",
            )
        )
        for exchange in qa_history
    )

    seed = "|".join(
        [
            str(sender_email),
            str(location_name),
            str(
                current_summary.get(
                    "timestamp"
                )
            ),
            ",".join(
                receiver_emails
            ),
            qa_signature,
        ]
    )

    return str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            seed,
        )
    )


def send_skybrief_email(
    api_key,
    sender_email,
    sender_name,
    receiver_emails,
    location_name,
    current_summary,
    daily_summary_df,
    ai_text,
    qa_history,
):
    """
    Send one final SkyBrief to 1–20 recipients.

    Uses one Brevo batch API request.
    """

    cleaned_emails = [
        email.strip()
        for email in receiver_emails
        if email.strip()
    ]

    cleaned_emails = list(
        dict.fromkeys(
            cleaned_emails
        )
    )


    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    if not cleaned_emails:
        raise ValueError(
            "At least one receiver email is required."
        )

    if len(cleaned_emails) > 20:
        raise ValueError(
            "SkyBrief supports up to 20 recipients."
        )

    invalid_emails = [
        email
        for email in cleaned_emails
        if not is_valid_email(email)
    ]

    if invalid_emails:
        raise ValueError(
            "Invalid receiver email(s): "
            + ", ".join(
                invalid_emails
            )
        )


    # --------------------------------------------------------
    # Build final HTML snapshot
    # --------------------------------------------------------

    html_content = build_skybrief_email(
        location_name=location_name,
        current_summary=current_summary,
        daily_summary_df=daily_summary_df,
        ai_text=ai_text,
        qa_history=qa_history,
    )


    # --------------------------------------------------------
    # Idempotency protection
    # --------------------------------------------------------

    idempotency_key = (
        _build_idempotency_key(
            sender_email=sender_email,
            location_name=location_name,
            current_summary=current_summary,
            receiver_emails=cleaned_emails,
            qa_history=qa_history,
        )
    )


    # --------------------------------------------------------
    # One private message version per recipient
    # --------------------------------------------------------

    message_versions = [
        {
            "to": [
                {
                    "email": email
                }
            ]
        }
        for email in cleaned_emails
    ]


    payload = {
        "sender": {
            "name": sender_name,
            "email": sender_email,
        },

        "subject": (
            f"☁️ SkyBrief AI · "
            f"{location_name} Weather Pulse"
        ),

        "htmlContent": html_content,

        "messageVersions": (
            message_versions
        ),

        "headers": {
            "idempotencyKey": (
                idempotency_key
            )
        },

        "tags": [
            "skybrief-ai"
        ],
    }


    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json",
    }


    # --------------------------------------------------------
    # Send
    #
    # Normally: ONE API request.
    #
    # Retry only for:
    # - 429 rate limit
    # - temporary 5xx Brevo errors
    # --------------------------------------------------------

    response = None

    for attempt in range(3):

        response = requests.post(
            BREVO_EMAIL_URL,
            headers=headers,
            json=payload,
            timeout=30,
        )


        if response.status_code < 400:
            break


        retryable = (
            response.status_code == 429
            or response.status_code >= 500
        )


        # Permanent error such as 400/401/etc.
        if not retryable:

            raise RuntimeError(
                f"Brevo API error "
                f"{response.status_code}: "
                f"{response.text}"
            )


        # Final failed retry.
        if attempt == 2:

            raise RuntimeError(
                f"Brevo API error "
                f"{response.status_code}: "
                f"{response.text}"
            )


        retry_after = (
            response.headers.get(
                "Retry-After"
            )
        )


        try:
            delay = float(
                retry_after
            )

        except (
            TypeError,
            ValueError,
        ):
            delay = (
                1.5 * (attempt + 1)
            )


        delay = min(
            max(
                delay,
                1.0,
            ),
            6.0,
        )

        time.sleep(
            delay
        )


    if response is None:
        raise RuntimeError(
            "Brevo request was not executed."
        )


    if response.status_code >= 400:

        raise RuntimeError(
            f"Brevo API error "
            f"{response.status_code}: "
            f"{response.text}"
        )


    result = response.json()


    return {
        "brevo_response": result,

        "recipient_count": len(
            cleaned_emails
        ),

        "recipients": (
            cleaned_emails
        ),

        "idempotency_key": (
            idempotency_key
        ),
    }
