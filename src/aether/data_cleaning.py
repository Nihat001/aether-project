# src/aether/data_cleaning.py

from __future__ import annotations

from typing import Dict, List, Tuple

import pandas as pd


class DataCleaner:
    """
    All validation/cleaning using pandas.
    """

    @staticmethod
    def clean_historical(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, float]]:
        initial = len(df)

        # Drop rows with missing critical values
        df = df.dropna(subset=["sensor_id", "timestamp"])

        # Remove negative pollutant values (vectorized)
        for col in ["pm25", "pm10", "no2", "o3"]:
            if col in df.columns:
                df = df[df[col] >= 0]

        # Filter extreme outliers for PM2.5
        if "pm25" in df.columns:
            df = df[df["pm25"] <= 500]

        # NO2 ignore  abov 400
        if "no2" in df.columns:
            df = df[df["no2"] <= 400]

        # Convert timestamp to datetime
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.dropna(subset=["timestamp"])

        final = len(df)
        stats = {
            "initial_rows": float(initial),
            "final_rows": float(final),
            "dropped_rows": float(initial - final),
            "percent_cleaned": float((initial - final) / initial * 100) if initial else 0.0,
        }
        return df, stats

    @staticmethod
    def validate_readings(readings: Dict[str, float]) -> Tuple[bool, List[str]]:
        """
        Validate a single reading payload via pandas.
        Returns (ok, errors).
        """
        errors: List[str] = []
        if not readings:
            errors.append("Readings dictionary is empty.")
            return False, errors

        s = pd.Series(readings, dtype="float64")

        # No negative values
        if (s < 0).any():
            errors.append("Negative pollutant values are not allowed.")

        # Example extra sanity: too extreme pm25
        if "pm25" in s and s["pm25"] > 500:
            errors.append("PM2.5 value too large (>500).")

        # Capping NO2 at 400
        if "no2" in s and s["no2"] > 400:
            errors.append("NO2 value too large (>400).")

        return len(errors) == 0, errors
