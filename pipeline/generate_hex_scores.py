"""
Stage 3: Build per-hex GeoJSON with refreshed GridScore values.

Reads:
  - computation/datacenter_scores_real.csv  (from Stage 1)
  - computation/hex_weather_data_all.csv    (from Stage 2)
  - frontend/public/data/score_map.json     (base hex geometries)

Writes:
  - frontend/public/data/score_map_hex.json (final output for frontend)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def _minmax_clamped(
    series: pd.Series, lower_q: float = 0.01, upper_q: float = 0.99
) -> pd.Series:
    """Normalize to 0-1 after clipping to percentile bounds."""
    lo, hi = series.quantile(lower_q), series.quantile(upper_q)
    rng = hi - lo if hi > lo else 1
    return ((series.clip(lo, hi) - lo) / rng).fillna(0.5)


def _load_base_data(
    scores_path: Path, hex_climate_path: Path, base_map_path: Path
):
    scores_df = pd.read_csv(scores_path)
    hex_df = pd.read_csv(hex_climate_path)

    with base_map_path.open() as f:
        fc = json.load(f)
    features = fc.get("features", [])

    lat_lon_rows = []
    region_rows = []
    for feat in features:
        props = feat.get("properties", {}) or {}
        hid = props.get("hex_id")
        lat = props.get("lat")
        lon = props.get("lon")
        reg = props.get("region")
        if hid is not None and lat is not None and lon is not None:
            lat_lon_rows.append({"hex_id": hid, "lat": lat, "lon": lon})
        if hid is not None and reg is not None:
            region_rows.append({"hex_id": hid, "region": reg})

    latlon_df = pd.DataFrame(lat_lon_rows).drop_duplicates("hex_id")
    region_df = pd.DataFrame(region_rows).drop_duplicates("hex_id")

    hex_df = hex_df.merge(latlon_df, on="hex_id", how="left")
    if "region" in hex_df.columns:
        hex_df = hex_df.drop(columns=["region"])
    hex_df = hex_df.merge(region_df, on="hex_id", how="left")

    return scores_df, hex_df, features


def _assign_region_if_missing(
    hex_df: pd.DataFrame, scores_df: pd.DataFrame
) -> pd.DataFrame:
    if hex_df["region"].notna().all():
        return hex_df

    region_centroids = scores_df[["region", "lat", "lon"]].rename(
        columns={"lat": "region_lat", "lon": "region_lon"}
    )
    regions_np = region_centroids[["region", "region_lat", "region_lon"]].to_numpy()

    def haversine_vec(lat, lon, region_mat):
        phi1 = np.radians(lat)
        phi2 = np.radians(region_mat[:, 1].astype(float))
        dphi = np.radians(region_mat[:, 1].astype(float) - lat)
        dlambda = np.radians(region_mat[:, 2].astype(float) - lon)
        a = (
            np.sin(dphi / 2.0) ** 2
            + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2.0) ** 2
        )
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        return 6371000 * c

    regions = []
    dists = []
    for _, row in hex_df.iterrows():
        lat, lon = row.get("lat"), row.get("lon")
        if pd.isna(lat) or pd.isna(lon):
            regions.append(row.get("region"))
            dists.append(np.nan)
            continue
        dist_arr = haversine_vec(lat, lon, regions_np)
        idx = np.argmin(dist_arr)
        regions.append(regions_np[idx, 0])
        dists.append(float(dist_arr[idx]))

    hex_df = hex_df.copy()
    hex_df["region"] = hex_df["region"].fillna(
        pd.Series(regions, index=hex_df.index)
    )
    hex_df["dist_to_region_m"] = dists
    return hex_df


def _compute_hex_scores(hex_df: pd.DataFrame) -> pd.DataFrame:
    hex_df = hex_df.copy()
    hex_df["temp_norm"] = _minmax_clamped(hex_df["local_temp_c"])
    hex_df["temp_cool_score"] = 1 - hex_df["temp_norm"]
    hex_df["elev_norm"] = _minmax_clamped(hex_df["elevation_m"])

    TEMP_WEIGHT = 0.15
    ELEV_WEIGHT = 0.05
    SMOOTH_K = 20
    SMOOTH_BLEND = 0.25

    hex_df["sustainability_hex"] = (
        hex_df["sustainability"]
        + hex_df["temp_cool_score"] * TEMP_WEIGHT
        + hex_df["elev_norm"] * ELEV_WEIGHT
    )
    hex_df["profitability_hex"] = hex_df["profitability"]
    hex_df["dc_score_hex"] = (
        0.6 * hex_df["sustainability_hex"] + 0.4 * hex_df["profitability_hex"]
    )

    coords = hex_df[["lat", "lon"]].to_numpy()
    values = hex_df["dc_score_hex"].to_numpy()

    def knn_smooth(coords_arr, vals, k=SMOOTH_K, self_weight=SMOOTH_BLEND):
        smoothed = np.array(vals, copy=True)
        valid = ~np.isnan(coords_arr).any(axis=1)
        valid_count = int(valid.sum())
        if valid_count < 2:
            return smoothed

        k_eff = max(1, min(k, valid_count - 1))
        coords_valid = coords_arr[valid]
        vals_valid = vals[valid]

        lat = np.radians(coords_valid[:, 0])[:, None]
        lon = np.radians(coords_valid[:, 1])[:, None]
        lat_T = lat.T
        lon_T = lon.T
        dphi = lat - lat_T
        dlambda = lon - lon_T
        a = (
            np.sin(dphi / 2.0) ** 2
            + np.cos(lat) * np.cos(lat_T) * np.sin(dlambda / 2.0) ** 2
        )
        dist = 2 * 6371000 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        np.fill_diagonal(dist, np.inf)

        knn_idx = np.argpartition(dist, kth=k_eff - 1, axis=1)[:, :k_eff]
        neighbor_means = vals_valid[knn_idx].mean(axis=1)
        smoothed_valid = self_weight * vals_valid + (1 - self_weight) * neighbor_means
        smoothed[valid] = smoothed_valid
        return smoothed

    hex_df["dc_score_hex_smooth"] = knn_smooth(coords, values)
    return hex_df


def _update_features(features: list, scored_df: pd.DataFrame) -> list:
    by_hex = {f.get("properties", {}).get("hex_id"): f for f in features}
    for _, row in scored_df.iterrows():
        hid = row["hex_id"]
        if hid not in by_hex:
            continue
        feat = by_hex[hid]
        props = feat.get("properties", {}) or {}

        props.update(
            {
                "hex_id": int(hid),
                "region": row.get("region"),
                "lat": row.get("lat"),
                "lon": row.get("lon"),
                "local_temp_c": row.get("local_temp_c"),
                "elevation_m": row.get("elevation_m"),
                "temp_cool_score": row.get("temp_cool_score"),
                "elev_norm": row.get("elev_norm"),
                "dist_to_region": row.get("dist_to_region_m"),
                "profitability": row.get("profitability_hex"),
                "sustainability": row.get("sustainability_hex"),
                "dc_score": row.get("dc_score_hex"),
                "dc_score_smooth": row.get("dc_score_hex_smooth"),
                "dc_score_temp": row.get("dc_score_hex"),
                # Propagate raw + normalized regional metrics for frontend
                "raw_renew": row.get("raw_renew"),
                "raw_price": row.get("raw_price"),
                "raw_load": row.get("raw_load"),
                "n_renew": row.get("n_renew"),
                "n_price": row.get("n_price"),
                "n_load": row.get("n_load"),
                "n_volatility": row.get("n_volatility"),
            }
        )
        feat["properties"] = props

    return features


def run(project_root: Path) -> Path:
    """
    Merge regional scores + hex weather into final GeoJSON.

    Returns the path to the output file.
    """
    scores_path = project_root / "computation" / "datacenter_scores_real.csv"
    hex_climate_path = project_root / "computation" / "hex_weather_data_all.csv"
    base_map_path = project_root / "frontend" / "public" / "data" / "score_map.json"
    output_path = project_root / "frontend" / "public" / "data" / "score_map_hex.json"

    logger.info("Loading base data...")
    logger.info("  Scores:  %s", scores_path)
    logger.info("  Climate: %s", hex_climate_path)
    logger.info("  Base map: %s", base_map_path)

    scores_df, hex_df, features = _load_base_data(
        scores_path, hex_climate_path, base_map_path
    )

    logger.info("Assigning regions to %d hexes...", len(hex_df))
    hex_df = _assign_region_if_missing(hex_df, scores_df)

    logger.info("Merging regional scores onto hex grid...")
    merged = hex_df.merge(scores_df, on="region", how="left", suffixes=("", "_region"))

    logger.info("Computing per-hex scores with KNN smoothing...")
    scored = _compute_hex_scores(merged)

    logger.info("Updating GeoJSON features...")
    updated_features = _update_features(features, scored)

    out_fc = {"type": "FeatureCollection", "features": updated_features}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(out_fc))
    logger.info("Wrote %s (%d features)", output_path, len(updated_features))

    return output_path
