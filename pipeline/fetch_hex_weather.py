"""
Stage 2: Fetch per-hex weather data (temperature + elevation) from Open-Meteo.

Reads:
  - US states GeoJSON from GitHub (to clip hex grid to continental US)
  - Open-Meteo API (30-day historical mean temp + elevation)

Writes:
  - computation/hex_weather_data_all.csv
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import requests
from shapely.geometry import Polygon

logger = logging.getLogger(__name__)

USA_URL = "https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json"
HEX_RADIUS = 50_000  # 50 km
MICRO_BATCH_SIZE = 100  # API limit per call
API_PAUSE = 1.0  # seconds between API calls


def _make_hex(center_x: float, center_y: float, radius: float) -> Polygon:
    angles = np.radians(np.arange(30, 390, 60))
    overlap_factor = 1.001
    return Polygon(
        [
            (
                center_x + radius * overlap_factor * np.cos(a),
                center_y + radius * overlap_factor * np.sin(a),
            )
            for a in angles
        ]
    )


def _build_hex_df() -> pd.DataFrame:
    """Build hex grid covering continental US and return centroids."""
    logger.info("Loading US boundary from %s", USA_URL)
    usa = gpd.read_file(USA_URL)
    usa_border = usa.union_all()
    usa_gdf = gpd.GeoDataFrame(geometry=[usa_border], crs="EPSG:4326")
    usa_proj = usa_gdf.to_crs("EPSG:5070")

    hex_height = np.sqrt(3) * HEX_RADIUS
    dx = np.sqrt(3) * HEX_RADIUS
    dy = 0.865 * hex_height

    minx, miny, maxx, maxy = usa_proj.total_bounds

    hexes = []
    row = 0
    y = miny - hex_height
    while y < maxy + hex_height:
        x_offset = (row % 2) * (dx / 2)
        x = minx - 2 * HEX_RADIUS
        while x < maxx + 2 * HEX_RADIUS:
            hexes.append(_make_hex(x + x_offset, y, HEX_RADIUS))
            x += dx
        y += dy
        row += 1

    hexgrid_proj = gpd.GeoDataFrame(geometry=hexes, crs="EPSG:5070")
    hex_us_proj = gpd.overlay(hexgrid_proj, usa_proj, how="intersection")
    hex_us = hex_us_proj.to_crs("EPSG:4326")
    centers = hex_us.to_crs("EPSG:5070").geometry.centroid
    centers_4326 = gpd.GeoSeries(centers, crs="EPSG:5070").to_crs("EPSG:4326")

    logger.info("Built hex grid with %d hexes", len(hex_us))
    return pd.DataFrame(
        {
            "hex_id": np.arange(len(hex_us)),
            "lat": centers_4326.y.values,
            "lon": centers_4326.x.values,
        }
    )


def _fetch_weather_batch(hex_df: pd.DataFrame) -> pd.DataFrame:
    """Fetch 30-day mean temp + elevation for all hexes via Open-Meteo."""
    lats = hex_df["lat"].tolist()
    lons = hex_df["lon"].tolist()
    ids = hex_df["hex_id"].tolist()

    weather_data = []

    for i in range(0, len(hex_df), MICRO_BATCH_SIZE):
        chunk_ids = ids[i : i + MICRO_BATCH_SIZE]
        chunk_lats = lats[i : i + MICRO_BATCH_SIZE]
        chunk_lons = lons[i : i + MICRO_BATCH_SIZE]

        params = {
            "latitude": ",".join(map(str, chunk_lats)),
            "longitude": ",".join(map(str, chunk_lons)),
            "daily": "temperature_2m_mean",
            "past_days": 30,
            "timezone": "auto",
        }

        try:
            r = requests.get(
                "https://api.open-meteo.com/v1/forecast", params=params, timeout=30
            )
            r.raise_for_status()
            responses = r.json()

            if not isinstance(responses, list):
                responses = [responses]

            for hex_id, resp in zip(chunk_ids, responses):
                daily_temps = resp.get("daily", {}).get("temperature_2m_mean", [])
                valid = [t for t in daily_temps if t is not None] if daily_temps else []
                avg_temp = sum(valid) / len(valid) if valid else float("nan")

                weather_data.append(
                    {
                        "hex_id": hex_id,
                        "local_temp_c": avg_temp,
                        "elevation_m": resp.get("elevation", np.nan),
                    }
                )

            batch_num = i // MICRO_BATCH_SIZE + 1
            total_batches = (len(hex_df) + MICRO_BATCH_SIZE - 1) // MICRO_BATCH_SIZE
            logger.info(
                "  Weather batch %d/%d complete (%d hexes)",
                batch_num,
                total_batches,
                len(chunk_ids),
            )
            time.sleep(API_PAUSE)

        except Exception as e:
            logger.error("  Error on weather batch starting at index %d: %s", i, e)

    return pd.DataFrame(weather_data)


def run(project_root: Path) -> Path:
    """
    Build hex grid and fetch weather data for each hex.

    Returns the path to the output CSV.
    """
    output_path = project_root / "computation" / "hex_weather_data_all.csv"

    hex_df = _build_hex_df()
    logger.info("Fetching weather data for %d hexes...", len(hex_df))

    weather_df = _fetch_weather_batch(hex_df)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    weather_df.to_csv(output_path, index=False)
    logger.info("Wrote %s (%d hexes)", output_path, len(weather_df))

    return output_path
