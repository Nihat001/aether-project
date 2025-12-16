# src/aether/visualization.py

from __future__ import annotations

from typing import Dict

import plotly.express as px
import pandas as pd


class MapVisualizer:
    def __init__(self, map_config: Dict, thresholds: Dict):
        self._map_config = map_config
        self._thresholds = thresholds

    def _category_for_pm25(self, pm25):
        if pd.isna(pm25):
            return "No data"

        safe = self._thresholds["pm25_safe"]
        moderate = self._thresholds["pm25_moderate"]
        danger = self._thresholds["pm25_danger"]

        if pm25 <= safe:
            return "Safe"
        if pm25 <= moderate:
            return "Moderate"
        if pm25 <= danger:
            return "Unhealthy"
        return "Dangerous"

    def create_map_html(self, df: pd.DataFrame, title: str = "Air Quality Map") -> str:
        if df.empty:
            # Give at least an empty map centered on NL-ish
            df = pd.DataFrame(
                [
                    {
                        "sensor_id": "no_data",
                        "lat": 52.1326,
                        "lon": 5.2913,
                        "pm25": None,
                        "pm10": None,
                        "no2": None,
                        "o3": None,
                        "category": "No data",
                    }
                ]
            )
        else:
            df = df.copy()
            df["category"] = df["pm25"].apply(self._category_for_pm25)
            # Format detailed readings for hover
            df["pm25_str"] = df["pm25"].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "N/A")
            df["pm10_str"] = df["pm10"].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "N/A")
            df["no2_str"] = df["no2"].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "N/A")
            df["o3_str"] = df["o3"].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "N/A")
            df["hover_text"] = (
                "<b>" + df["sensor_id"] + "</b><br>" +
                "Province: " + df["province"].fillna("Unknown") + "<br>" +
                "Region: " + df["region"].fillna("Unknown") + "<br>" +
                "Category: " + df["category"] + "<br><br>" +
                "<b>Detailed Readings (µg/m³)</b><br>" +
                "PM2.5: " + df["pm25_str"] + "<br>" +
                "PM10: " + df["pm10_str"] + "<br>" +
                "NO₂: " + df["no2_str"] + "<br>" +
                "O₃: " + df["o3_str"]
            )

        fig = px.scatter_mapbox(
            df,
            lat="lat",
            lon="lon",
            color="category",
            hover_name="sensor_id",
            hover_data={"hover_text": True, "pm25": False, "pm10": False, "no2": False, "o3": False, "lat": False, "lon": False, "province": False, "region": False, "category": False},
            custom_data=["hover_text"],
            zoom=self._map_config.get("default_zoom", 7),
            title=title,
        )

        # Custom hover template to show formatted text
        fig.update_traces(
            hovertemplate="<b style='font-size:12px'>%{customdata[0]}</b><extra></extra>",
            marker={"size": 10},
        )

        fig.update_layout(
            mapbox_style=self._map_config.get("map_style", "open-street-map"),
            margin={"r": 0, "t": 40, "l": 0, "b": 0},
        )

        return fig.to_html(include_plotlyjs="cdn", full_html=True)
