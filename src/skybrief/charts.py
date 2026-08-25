import pandas as pd
import plotly.graph_objects as go


def _add_day_separators(
    fig,
    forecast_df,
):
    """
    Add subtle midnight separators between forecast days.
    """

    datetimes = pd.to_datetime(
        forecast_df["datetime"]
    )

    days = sorted(
        datetimes.dt.normalize().unique()
    )

    for day in days[1:]:

        fig.add_vline(
            x=day,
            line_width=1,
            line_dash="dot",
            line_color="rgba(148,163,184,0.14)",
            layer="below",
        )


def _base_layout(fig):
    """
    Minimal SkyBrief chart canvas.
    Presentation titles live in Streamlit, not Plotly.
    """

    fig.update_layout(
        height=315,

        margin={
            "l": 42,
            "r": 20,
            "t": 28,
            "b": 38,
        },

        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",

        font={
            "family": "Inter, Arial, sans-serif",
            "color": "#CBD5E1",
            "size": 12,
        },

        hovermode="x unified",

        hoverlabel={
            "bgcolor": "#111827",
            "bordercolor": "#334155",
            "font": {
                "color": "#F8FAFC",
                "size": 12,
            },
        },

        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
            "font": {
                "size": 11,
                "color": "#CBD5E1",
            },
        },

        showlegend=True,
    )


    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        showline=False,

        tickformat="%a\n%d %b",

        dtick=24 * 60 * 60 * 1000,

        tickfont={
            "size": 11,
            "color": "#7C8CA5",
        },

        ticks="",
    )


def create_temperature_chart(
    forecast_df,
    location_name=None,
):
    """
    Air temperature + feels-like temperature.
    """

    fig = go.Figure()


    # --------------------------------------------------------
    # Air temperature
    # --------------------------------------------------------

    fig.add_trace(
        go.Scatter(
            x=forecast_df["datetime"],

            y=forecast_df[
                "temperature_celsius"
            ],

            name="Air",

            mode="lines",

            line={
                "color": "#F6C453",
                "width": 3.2,
                "shape": "spline",
                "smoothing": 0.35,
            },

            hovertemplate=(
                "<b>%{x|%a, %d %b · %I:%M %p}</b>"
                "<br>Air&nbsp;&nbsp;%{y:.1f}°C"
                "<extra></extra>"
            ),
        )
    )


    # --------------------------------------------------------
    # Feels-like
    # --------------------------------------------------------

    fig.add_trace(
        go.Scatter(
            x=forecast_df["datetime"],

            y=forecast_df[
                "feels_like_celsius"
            ],

            name="Feels",

            mode="lines",

            line={
                "color": "#FF879D",
                "width": 2.4,
                "dash": "dash",
                "shape": "spline",
                "smoothing": 0.30,
            },

            hovertemplate=(
                "<b>%{x|%a, %d %b · %I:%M %p}</b>"
                "<br>Feels&nbsp;&nbsp;%{y:.1f}°C"
                "<extra></extra>"
            ),
        )
    )


    values = pd.concat(
        [
            forecast_df[
                "temperature_celsius"
            ],
            forecast_df[
                "feels_like_celsius"
            ],
        ]
    )


    minimum = values.min()
    maximum = values.max()

    padding = max(
        (maximum - minimum) * 0.10,
        1.2,
    )


    fig.update_yaxes(
        range=[
            minimum - padding,
            maximum + padding,
        ],

        ticksuffix="°",

        showgrid=True,

        gridcolor="rgba(148,163,184,0.09)",

        zeroline=False,

        tickfont={
            "size": 11,
            "color": "#7C8CA5",
        },

        ticks="",
    )


    _add_day_separators(
        fig,
        forecast_df,
    )

    _base_layout(fig)

    return fig


def create_rain_humidity_chart(
    forecast_df,
    location_name=None,
):
    """
    Rain probability + humidity.

    Rain probability uses a STEP line because
    OpenWeather provides discrete 3-hour probabilities.
    """

    fig = go.Figure()


    # --------------------------------------------------------
    # Rain probability
    # --------------------------------------------------------

    fig.add_trace(
        go.Scatter(
            x=forecast_df["datetime"],

            y=forecast_df[
                "rain_probability_percent"
            ],

            name="Rain",

            mode="lines",

            line={
                "color": "#35C5D9",
                "width": 2.4,
                "dash": "dash",
                "shape": "hv",
            },

            fill="tozeroy",

            fillcolor=(
                "rgba(53,197,217,0.055)"
            ),

            hovertemplate=(
                "<b>%{x|%a, %d %b · %I:%M %p}</b>"
                "<br>Rain&nbsp;&nbsp;%{y:.0f}%"
                "<extra></extra>"
            ),
        )
    )


    # --------------------------------------------------------
    # Humidity
    # --------------------------------------------------------

    fig.add_trace(
        go.Scatter(
            x=forecast_df["datetime"],

            y=forecast_df[
                "humidity_percent"
            ],

            name="Humidity",

            mode="lines",

            line={
                "color": "#9D8CFF",
                "width": 2.8,
                "shape": "spline",
                "smoothing": 0.30,
            },

            hovertemplate=(
                "<b>%{x|%a, %d %b · %I:%M %p}</b>"
                "<br>Humidity&nbsp;&nbsp;%{y:.0f}%"
                "<extra></extra>"
            ),
        )
    )


    fig.update_yaxes(
        range=[0, 100],

        tickvals=[
            0,
            25,
            50,
            75,
            100,
        ],

        ticksuffix="%",

        showgrid=True,

        gridcolor="rgba(148,163,184,0.09)",

        zeroline=False,

        tickfont={
            "size": 11,
            "color": "#7C8CA5",
        },

        ticks="",
    )


    _add_day_separators(
        fig,
        forecast_df,
    )

    _base_layout(fig)

    return fig