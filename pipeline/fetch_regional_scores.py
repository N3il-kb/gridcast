"""
Stage 1: Fetch per-region datacenter suitability scores from EIA + Open-Meteo APIs.

Reads:
  - EIA API v2 (demand, fuel mix, wholesale prices)
  - Open-Meteo API (60-day mean temperature)
  - Fallback: cache/eia_{REGION}_hourly.csv

Writes:
  - computation/datacenter_scores_real.csv
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import requests

logger = logging.getLogger(__name__)

EIA_BASE_URL = "https://api.eia.gov/v2/electricity/"

# Codes for carbon-free energy sources
GREEN_CODES = {"SUN", "WND", "WAT", "GEO", "NUC"}

REGION_COORDS = {
    "CAL": (36.5, -119.5),
    "CAR": (35.5, -80.0),
    "CENT": (38.5, -94.5),
    "FLA": (28.0, -82.0),
    "MIDA": (39.0, -77.0),
    "MIDW": (42.0, -89.0),
    "NE": (42.5, -72.5),
    "NY": (42.9, -75.3),
    "NW": (45.5, -120.5),
    "SE": (33.0, -84.0),
    "SW": (36.0, -111.5),
    "TEN": (36.0, -86.0),
    "TEX": (31.0, -99.0),
}


def _fetch_eia_hourly(region: str, api_key: str, cache_dir: Path) -> pd.DataFrame:
    """Fetch 90-day hourly demand (MW) from EIA, with CSV cache fallback."""
    url = EIA_BASE_URL + "rto/region-data/data/"
    end = datetime.utcnow()
    start = end - timedelta(days=90)

    params = {
        "api_key": api_key,
        "data[0]": "value",
        "facets[respondent][]": region,
        "frequency": "hourly",
        "start": start.strftime("%Y-%m-%dT%H"),
        "end": end.strftime("%Y-%m-%dT%H"),
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "length": 5000,
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json().get("response", {}).get("data", [])
        df = pd.DataFrame(data)
        if not df.empty:
            df["datetime"] = pd.to_datetime(df["period"])
            df["demand_MW"] = df["value"].astype(float)
            # Update cache on success
            cache_path = cache_dir / f"eia_{region.lower()}_hourly.csv"
            df.to_csv(cache_path, index=False)
            return df.sort_values("datetime")
        return pd.DataFrame()
    except Exception as e:
        logger.warning("Demand fetch failed for %s: %s — trying cache", region, e)
        cache_path = cache_dir / f"eia_{region.lower()}_hourly.csv"
        if cache_path.exists():
            df = pd.read_csv(cache_path)
            if "datetime" not in df.columns and "period" in df.columns:
                df["datetime"] = pd.to_datetime(df["period"])
            if "demand_MW" not in df.columns and "value" in df.columns:
                df["demand_MW"] = df["value"].astype(float)
            return df.sort_values("datetime") if not df.empty else pd.DataFrame()
        return pd.DataFrame()


def _fetch_eia_fuelmix(region: str, api_key: str) -> float:
    """Fetch carbon-free energy percentage (0-100) from latest hour."""
    url = EIA_BASE_URL + "rto/fuel-type-data/data/"
    end = datetime.utcnow()
    start = end - timedelta(hours=24)

    params = {
        "api_key": api_key,
        "data[0]": "value",
        "facets[respondent][]": region,
        "frequency": "hourly",
        "start": start.strftime("%Y-%m-%dT%H"),
        "end": end.strftime("%Y-%m-%dT%H"),
        "length": 500,
    }

    try:
        r = requests.get(url, params=params, timeout=30)
        data = r.json().get("response", {}).get("data", [])
        if not data:
            return float("nan")

        df = pd.DataFrame(data)
        df["value"] = df["value"].astype(float)

        latest_time = df["period"].max()
        current_mix = df[df["period"] == latest_time]

        total = current_mix["value"].sum()
        if total == 0:
            return 0.0

        clean = current_mix[current_mix["fueltype"].isin(GREEN_CODES)]["value"].sum()
        return (clean / total) * 100.0
    except Exception:
        logger.warning("Fuel mix fetch failed for %s", region)
        return float("nan")


def _fetch_eia_price(region: str, api_key: str) -> float:
    """Fetch latest wholesale LMP price ($/MWh)."""
    url = EIA_BASE_URL + "wholesale-markets-data/data/"
    params = {
        "api_key": api_key,
        "data[0]": "value",
        "facets[respondent][]": region,
        "frequency": "hourly",
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "length": 10,
    }
    try:
        r = requests.get(url, params=params, timeout=5)
        data = r.json().get("response", {}).get("data", [])
        if data:
            vals = [float(x["value"]) for x in data if x.get("value")]
            return np.mean(vals) if vals else float("nan")
    except Exception:
        pass
    return float("nan")


def _fetch_temperature(lat: float, lon: float) -> float:
    """Fetch 60-day mean temperature from Open-Meteo."""
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "temperature_2m_mean",
            "past_days": 60,
        }
        r = requests.get(url, params=params, timeout=10)
        temps = r.json().get("daily", {}).get("temperature_2m_mean", [])
        valid = [t for t in temps if t is not None]
        return np.mean(valid) if valid else np.nan
    except Exception:
        return np.nan


def _normalize(series: pd.Series, invert: bool = False) -> pd.Series:
    min_v, max_v = series.min(), series.max()
    if max_v == min_v:
        return pd.Series(0.5, index=series.index)
    norm = (series - min_v) / (max_v - min_v)
    return (1 - norm) if invert else norm


def run(project_root: Path) -> Path:
    """
    Fetch regional scores from APIs and write datacenter_scores_real.csv.

    Returns the path to the output CSV.
    """
    api_key = os.getenv("EIA_API_KEY")
    if not api_key:
        raise RuntimeError("EIA_API_KEY environment variable is not set")

    cache_dir = project_root / "cache"
    cache_dir.mkdir(exist_ok=True)
    output_path = project_root / "computation" / "datacenter_scores_real.csv"

    logger.info("Fetching real data for %d regions...", len(REGION_COORDS))
    records = []

    for region, (lat, lon) in REGION_COORDS.items():
        logger.info("  Region %s (%.1f, %.1f)", region, lat, lon)

        df_demand = _fetch_eia_hourly(region, api_key, cache_dir)
        raw_renew = _fetch_eia_fuelmix(region, api_key)
        raw_price = _fetch_eia_price(region, api_key)
        raw_temp = _fetch_temperature(lat, lon)

        if not df_demand.empty:
            raw_load = df_demand["demand_MW"].iloc[-1]
            raw_volatility = df_demand["demand_MW"].tail(24).std()
            raw_peak = df_demand["demand_MW"].max()
        else:
            raw_load, raw_volatility, raw_peak = np.nan, np.nan, np.nan

        # Fallback: proxy price using load stress
        if np.isnan(raw_price) and not np.isnan(raw_load):
            raw_price = (raw_load / 1000) * 2.5

        records.append(
            {
                "region": region,
                "lat": lat,
                "lon": lon,
                "raw_price": raw_price,
                "raw_load": raw_load,
                "raw_volatility": raw_volatility,
                "raw_peak": raw_peak,
                "raw_renew": raw_renew,
                "raw_temp": raw_temp,
            }
        )

    dc_df = pd.DataFrame(records)

    # Mean imputation for missing values
    dc_df = dc_df.fillna(dc_df.mean(numeric_only=True))

    # Normalize: 0 = bad, 1 = good
    dc_df["n_price"] = _normalize(dc_df["raw_price"], invert=True)
    dc_df["n_load"] = _normalize(dc_df["raw_load"], invert=True)
    dc_df["n_volatility"] = _normalize(dc_df["raw_volatility"], invert=True)
    dc_df["n_temp"] = _normalize(dc_df["raw_temp"], invert=True)
    dc_df["n_renew"] = _normalize(dc_df["raw_renew"], invert=False)

    # Profitability (40% of final score)
    dc_df["profitability"] = (
        0.40 * dc_df["n_price"]
        + 0.30 * dc_df["n_load"]
        + 0.30 * dc_df["n_volatility"]
    )

    # Sustainability (60% of final score)
    dc_df["sustainability"] = 0.70 * dc_df["n_renew"] + 0.30 * dc_df["n_temp"]

    # Final score
    dc_df["dc_score"] = 0.40 * dc_df["profitability"] + 0.60 * dc_df["sustainability"]

    dc_df = dc_df.sort_values("dc_score", ascending=False).reset_index(drop=True)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    dc_df.to_csv(output_path, index=False)
    logger.info("Wrote %s (%d regions)", output_path, len(dc_df))

    return output_path
