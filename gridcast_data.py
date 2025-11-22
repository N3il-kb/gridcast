"""
Build a GridCast dataframe from real EIA v2 and Open-Meteo data.

Outputs a pandas DataFrame indexed by region with the raw metrics needed to
compute the Datacenter Score (60% Sustainability / 40% Profitability).
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Mapping, Optional, Tuple

import pandas as pd
import requests

# Region centroids for weather lookups
REGION_COORDS: Dict[str, Tuple[float, float]] = {
    "CAL": (36.5, -119.5),
    "TEX": (31.0, -99.0),
    "NY": (42.9, -75.3),
    "PJM": (40.0, -78.5),
    "NE": (42.5, -71.5),
    "MISO": (41.0, -90.0),
    "SPP": (37.5, -96.5),
    "NW": (45.5, -120.5),
    "SW": (36.0, -111.5),
    "SE": (33.0, -84.0),
}

# Representative wholesale hubs per region
WHOLESALE_HUBS: Dict[str, Mapping[str, str]] = {
    "CAL": {"market": "DA", "location": "TH_NP15"},
    "TEX": {"market": "RTM", "location": "HB_HOUSTON"},
    "NY": {"market": "DA", "location": "NYISO_ZONE_J"},
    "PJM": {"market": "DA", "location": "PJM WEST HUB"},
    "NE": {"market": "DA", "location": "ISONE_HUB"},
    "MISO": {"market": "RT", "location": "MISO INDIANA.HUB"},
    "SPP": {"market": "RTBM", "location": "SPP NORTH HUB"},
    "NW": {"market": "RT", "location": "PACW"},
    "SW": {"market": "RT", "location": "AZPS"},
    "SE": {"market": "RT", "location": "SOCO"},
}

# Emissions factors in lbs/MWh
EMISSIONS_LB_PER_MWH: Dict[str, float] = {
    "COAL": 2200.0,
    "COL": 2200.0,
    "NG": 900.0,
    "NATURAL GAS": 900.0,
    "GAS": 900.0,
    "OIL": 1600.0,
    "PET": 1600.0,
}

EIA_BASE = "https://api.eia.gov/v2"


def _require_api_key() -> str:
    api_key = os.getenv("EIA_API_KEY")
    if not api_key:
        raise RuntimeError("EIA_API_KEY environment variable is required.")
    return api_key


def _request_eia(path: str, params: Mapping[str, str]) -> List[Mapping[str, str]]:
    merged = {"api_key": _require_api_key(), **params}
    url = f"{EIA_BASE}/{path}/data/"
    resp = requests.get(url, params=merged, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    return payload.get("response", {}).get("data", []) or []


def _to_timestamp(value: str) -> pd.Timestamp:
    return pd.to_datetime(value, utc=True)


def fetch_latest_fuel_mix(region: str) -> Tuple[Optional[pd.Timestamp], Dict[str, float]]:
    """Return timestamp and fuel mix (MW) for the most recent hour."""
    try:
        end = datetime.utcnow()
        start = end - timedelta(days=2)
        data = _request_eia(
            "electricity/rto/fuel-type-data",
            {
                "facets[respondent][]": region,
                "frequency": "hourly",
                "start": start.strftime("%Y-%m-%dT%H"),
                "end": end.strftime("%Y-%m-%dT%H"),
                "sort[0][column]": "period",
                "sort[0][direction]": "desc",
                "length": 500,
            },
        )
        df = pd.DataFrame(data)
        if df.empty:
            return None, {}
        df["period"] = df["period"].apply(_to_timestamp)
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna(subset=["value"])
        if df.empty:
            return None, {}
        latest_ts = df["period"].max()
        df_latest = df[df["period"] == latest_ts]
        mix = df_latest.groupby("fueltype")["value"].sum().to_dict()
        return latest_ts, {k: float(v) for k, v in mix.items()}
    except Exception:
        return None, {}


def fetch_demand_series(region: str, days: int = 30) -> Optional[pd.DataFrame]:
    """Return demand series for the last `days` days."""
    try:
        end = datetime.utcnow()
        start = end - timedelta(days=days)
        data = _request_eia(
            "electricity/rto/region-data",
            {
                "facets[respondent][]": region,
                "frequency": "hourly",
                "start": start.strftime("%Y-%m-%dT%H"),
                "end": end.strftime("%Y-%m-%dT%H"),
                "sort[0][column]": "period",
                "sort[0][direction]": "asc",
                "length": 5000,
            },
        )
        df = pd.DataFrame(data)
        if df.empty:
            return None
        df["period"] = df["period"].apply(_to_timestamp)
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna(subset=["value"])
        if df.empty:
            return None
        return df[["period", "value"]].sort_values("period").reset_index(drop=True)
    except Exception:
        return None


def fetch_latest_price(region: str) -> Tuple[Optional[pd.Timestamp], Optional[float]]:
    """Return latest wholesale LMP price for the region's representative hub."""
    hub = WHOLESALE_HUBS.get(region, {"market": "DA", "location": region})
    try:
        end = datetime.utcnow()
        start = end - timedelta(days=5)
        data = _request_eia(
            "electricity/wholesale-markets-data",
            {
                "facets[market][]": hub.get("market", "DA"),
                "facets[location][]": hub.get("location", region),
                "frequency": "hourly",
                "start": start.strftime("%Y-%m-%dT%H"),
                "end": end.strftime("%Y-%m-%dT%H"),
                "sort[0][column]": "period",
                "sort[0][direction]": "desc",
                "length": 50,
            },
        )
        if not data:
            return None, None
        df = pd.DataFrame(data)
        df["period"] = df["period"].apply(_to_timestamp)
        value_field = next((c for c in ("lmp", "value", "price") if c in df.columns), None)
        if value_field is None:
            return None, None
        df[value_field] = pd.to_numeric(df[value_field], errors="coerce")
        df = df.dropna(subset=[value_field])
        if df.empty:
            return None, None
        latest = df.sort_values("period").iloc[-1]
        return latest["period"], float(latest[value_field])
    except Exception:
        return None, None


def fetch_temperature(lat: float, lon: float) -> Optional[float]:
    """Return current temperature in Celsius from Open-Meteo."""
    try:
        resp = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m",
                "timezone": "UTC",
            },
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        current = data.get("current", {}) or data.get("current_weather", {})
        if "temperature_2m" in current:
            return float(current["temperature_2m"])
        if "temperature" in current:
            return float(current["temperature"])
        return None
    except Exception:
        return None


def compute_renewable_pct(fuel_mix: Mapping[str, float]) -> Optional[float]:
    if not fuel_mix:
        return None
    total = sum(fuel_mix.values())
    if total <= 0:
        return None
    renewable_keys = {"SUN", "WND", "WAT", "HYDRO", "NUC", "SOLAR", "WIND", "HYD", "NUCLEAR"}
    renew = sum(v for k, v in fuel_mix.items() if k.upper() in renewable_keys)
    return renew / total


def compute_co2_intensity(fuel_mix: Mapping[str, float]) -> Optional[float]:
    if not fuel_mix:
        return None
    total = sum(fuel_mix.values())
    if total <= 0:
        return None
    weighted = 0.0
    for fuel, value in fuel_mix.items():
        factor = EMISSIONS_LB_PER_MWH.get(fuel.upper(), 0.0)
        weighted += value * factor
    return weighted / total


def build_gridcast_df(regions: Optional[Iterable[str]] = None) -> pd.DataFrame:
    """Build the GridCast DataFrame."""
    region_list = list(regions) if regions is not None else list(REGION_COORDS.keys())
    records = []
    for region in region_list:
        demand_series = fetch_demand_series(region)
        demand_ts = None
        demand_now = None
        stress_pct = None
        if demand_series is not None and not demand_series.empty:
            latest = demand_series.iloc[-1]
            demand_ts = latest["period"]
            demand_now = float(latest["value"])
            max_demand = demand_series["value"].max()
            if max_demand and max_demand > 0:
                stress_pct = demand_now / max_demand
        fuel_ts, fuel_mix = fetch_latest_fuel_mix(region)
        renewable_pct = compute_renewable_pct(fuel_mix)
        co2_intensity = compute_co2_intensity(fuel_mix)
        price_ts, price = fetch_latest_price(region)
        lat_lon = REGION_COORDS.get(region)
        temp_c = fetch_temperature(*lat_lon) if lat_lon else None
        timestamp = demand_ts or price_ts or fuel_ts
        records.append(
            {
                "region": region,
                "timestamp": timestamp,
                "price_usd": price,
                "demand_mw": demand_now,
                "grid_stress_pct": stress_pct,
                "renewable_pct": renewable_pct,
                "co2_intensity": co2_intensity,
                "temp_c": temp_c,
            }
        )
    return pd.DataFrame(records, columns=["region", "timestamp", "price_usd", "demand_mw", "grid_stress_pct", "renewable_pct", "co2_intensity", "temp_c"])


if __name__ == "__main__":
    df = build_gridcast_df()
    print(df)
