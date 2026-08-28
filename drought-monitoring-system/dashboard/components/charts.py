from collections.abc import Iterable

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


PLOTLY_CONFIG = {
    "displayModeBar": False,
    "responsive": True,
    "scrollZoom": False,
}

COLORS = {
    "green": "#5DDB8A",
    "green_soft": "#A7F3C2",
    "brown": "#B58A64",
    "amber": "#F2B95F",
    "red": "#FF7A7A",
    "blue": "#71B7FF",
    "muted": "#93AA9B",
    "grid": "rgba(173, 214, 188, 0.09)",
    "text": "#DDE9E0",
}


def apply_chart_theme(
    figure: go.Figure,
    height: int = 340,
    show_legend: bool = False,
) -> go.Figure:
    figure.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=20, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, Inter, sans-serif", color=COLORS["text"]),
        hoverlabel=dict(
            bgcolor="#123026",
            bordercolor="rgba(93,219,138,.28)",
            font=dict(color="#EDF7F0", family="DM Sans"),
        ),
        showlegend=show_legend,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color=COLORS["muted"]),
        ),
        hovermode="x unified",
    )

    figure.update_xaxes(
        showgrid=False,
        zeroline=False,
        color=COLORS["muted"],
        tickfont=dict(size=11),
        fixedrange=True,
    )
    figure.update_yaxes(
        gridcolor=COLORS["grid"],
        zeroline=False,
        color=COLORS["muted"],
        tickfont=dict(size=11),
        fixedrange=True,
    )
    return figure


def soil_moisture_chart(frame: pd.DataFrame) -> go.Figure:
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=frame["created_at"],
            y=frame["soil_moisture"],
            name="Soil moisture",
            mode="lines",
            line=dict(color=COLORS["green"], width=2.6),
            fill="tozeroy",
            fillcolor="rgba(93, 219, 138, 0.08)",
            hovertemplate="%{y:.1f}%<extra></extra>",
        )
    )
    figure.add_hrect(
        y0=0,
        y1=20,
        fillcolor="rgba(255, 122, 122, 0.05)",
        line_width=0,
    )
    figure.add_hline(
        y=20,
        line_color="rgba(255, 122, 122, 0.45)",
        line_dash="dot",
        annotation_text="Critical 20%",
        annotation_font_color=COLORS["red"],
        annotation_position="top left",
    )
    figure.update_yaxes(title=None, ticksuffix="%", range=[0, 70])
    return apply_chart_theme(figure, height=350)


def water_level_chart(frame: pd.DataFrame) -> go.Figure:
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=frame["created_at"],
            y=frame["water_level"],
            name="Water level",
            mode="lines",
            line=dict(color=COLORS["blue"], width=2.6),
            fill="tozeroy",
            fillcolor="rgba(113, 183, 255, 0.07)",
            hovertemplate="%{y:.1f}%<extra></extra>",
        )
    )
    figure.add_hline(
        y=5,
        line_color="rgba(255, 122, 122, 0.45)",
        line_dash="dot",
        annotation_text="Critical 5%",
        annotation_font_color=COLORS["red"],
        annotation_position="top left",
    )
    figure.update_yaxes(title=None, ticksuffix="%", range=[0, 100])
    return apply_chart_theme(figure, height=350)


def weather_forecast_chart(frame: pd.DataFrame) -> go.Figure:
    figure = make_subplots(specs=[[{"secondary_y": True}]])

    if "forecast_precipitation_7d_mm" in frame:
        x_values = frame["observed_at"]
        rain_values = frame["forecast_precipitation_7d_mm"]
        temperature_values = frame["forecast_temperature_max_3d_c"]
        rain_name = "Forecast rain, next 7 days"
        rain_hover = "%{y:.1f} mm forecast<extra></extra>"
        rain_suffix = " mm"
        rain_range = None
    else:
        x_values = frame["date"]
        rain_values = frame["rain_probability"]
        temperature_values = frame["maximum_temperature"]
        rain_name = "Rain probability"
        rain_hover = "%{y:.0f}% chance<extra></extra>"
        rain_suffix = "%"
        rain_range = [0, 100]

    figure.add_trace(
        go.Bar(
            x=x_values,
            y=rain_values,
            name=rain_name,
            marker=dict(color="rgba(113, 183, 255, 0.62)", line_width=0),
            hovertemplate=rain_hover,
        ),
        secondary_y=False,
    )
    figure.add_trace(
        go.Scatter(
            x=x_values,
            y=temperature_values,
            name="Maximum temperature, next 3 days",
            mode="lines+markers",
            line=dict(color=COLORS["amber"], width=2.3),
            marker=dict(size=6),
            hovertemplate="%{y:.1f}°C<extra></extra>",
        ),
        secondary_y=True,
    )
    figure.update_yaxes(
        ticksuffix=rain_suffix,
        range=rain_range,
        rangemode="tozero" if rain_range is None else None,
        secondary_y=False,
    )
    figure.update_yaxes(ticksuffix="°C", range=[20, 42], secondary_y=True)
    return apply_chart_theme(figure, height=350, show_legend=True)


def risk_distribution_chart(risk_levels: Iterable[str]) -> go.Figure:
    counts = pd.Series(list(risk_levels)).value_counts()
    order = ["normal", "medium", "high", "critical"]
    counts = counts.reindex(order, fill_value=0)

    figure = go.Figure(
        go.Pie(
            labels=[label.title() for label in order],
            values=counts.values,
            hole=0.72,
            marker=dict(
                colors=[
                    COLORS["green"],
                    COLORS["brown"],
                    COLORS["amber"],
                    COLORS["red"],
                ],
                line=dict(color="#0D2119", width=3),
            ),
            textinfo="none",
            hovertemplate="%{label}: %{value} readings<extra></extra>",
        )
    )
    figure.add_annotation(
        text=f"<b>{int(counts.sum())}</b><br><span style='font-size:11px'>readings</span>",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(color=COLORS["text"], size=19),
    )
    return apply_chart_theme(figure, height=300, show_legend=True)


def combined_environment_chart(frame: pd.DataFrame) -> go.Figure:
    figure = make_subplots(specs=[[{"secondary_y": True}]])
    figure.add_trace(
        go.Scatter(
            x=frame["created_at"],
            y=frame["temperature"],
            name="Temperature",
            line=dict(color=COLORS["amber"], width=2.2),
            hovertemplate="%{y:.1f}°C<extra></extra>",
        ),
        secondary_y=False,
    )
    figure.add_trace(
        go.Scatter(
            x=frame["created_at"],
            y=frame["humidity"],
            name="Humidity",
            line=dict(color=COLORS["blue"], width=2.0),
            hovertemplate="%{y:.1f}%<extra></extra>",
        ),
        secondary_y=True,
    )
    figure.update_yaxes(ticksuffix="°C", secondary_y=False)
    figure.update_yaxes(ticksuffix="%", range=[0, 100], secondary_y=True)
    return apply_chart_theme(figure, height=380, show_legend=True)


def daily_alert_chart(alerts: pd.DataFrame) -> go.Figure:
    if alerts.empty:
        grouped = pd.DataFrame({"date": [], "count": []})
    else:
        grouped = (
            alerts.assign(date=alerts["created_at"].dt.floor("D"))
            .groupby("date")
            .size()
            .reset_index(name="count")
        )

    figure = go.Figure(
        go.Bar(
            x=grouped["date"],
            y=grouped["count"],
            marker=dict(
                color=COLORS["amber"],
                line_width=0,
            ),
            hovertemplate="%{y} alerts<extra></extra>",
        )
    )
    figure.update_yaxes(dtick=1, rangemode="tozero")
    return apply_chart_theme(figure, height=320)
