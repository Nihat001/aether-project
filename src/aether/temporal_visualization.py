# src/aether/temporal_visualization.py

from __future__ import annotations

from typing import Dict

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


class TemporalVisualizer:
    @staticmethod
    def create_time_series(df: pd.DataFrame, sensor_id: str, title: str) -> str:
        """
        Time series for pm25, pm10, no2, o3 with range slider.
        """
        df = df.sort_values("timestamp")

        fig = go.Figure()

        for col in ["pm25", "pm10", "no2", "o3"]:
            if col in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df["timestamp"],
                        y=df[col],
                        mode="lines",
                        name=col.upper(),
                    )
                )

        fig.update_layout(
            title=title,
            xaxis={
                "title": "Time",
                "rangeslider": {"visible": True},
            },
            yaxis={"title": "Concentration (µg/m³)"},
            hovermode="x unified",
        )

        return fig.to_html(include_plotlyjs="cdn", full_html=True)

    @staticmethod
    def create_distribution_chart(
        df: pd.DataFrame,
        year: int,
        month: int,
        thresholds: Dict,
        title: str,
    ) -> str:
        """
        df columns: province, category, percentage
        """
        if df.empty:
            empty = pd.DataFrame(
                [{"province": "No data", "category": "No data", "percentage": 100}]
            )
            df = empty

        fig = px.bar(
            df,
            x="province",
            y="percentage",
            color="category",
            text="percentage",
            title=title,
            barmode="stack",
        )

        fig.update_layout(
            yaxis={"range": [0, 100], "title": "Percentage of readings (%)"},
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="inside")

        return fig.to_html(include_plotlyjs="cdn", full_html=True)
