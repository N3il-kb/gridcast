"""
Minimal Streamlit app to display the final datacenter score map
from `datacenter_score.ipynb` (continental US bounding box view).
"""

import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon
import streamlit as st
import folium
from streamlit.components.v1 import html
from branca.colormap import linear

# Geo source and constants
USA_URL = "https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json"
HEX_RADIUS_M = 50_000  # 50 km from center to vertex

# Continental US bounding box (matches the notebook cell)
MIN_LAT, MAX_LAT = 24.5, 49.5
MIN_LON, MAX_LON = -124.7, -66.9


def make_hex(center_x, center_y, radius):
    """Return a pointy-top hexagon polygon with a tiny overlap factor."""
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


def build_hexgrid(usa_proj):
    """Generate a hex grid covering the US border in projected coordinates."""
    hex_width = 2 * HEX_RADIUS_M
    hex_height = np.sqrt(3) * HEX_RADIUS_M
    dx = np.sqrt(3) * HEX_RADIUS_M  # horizontal spacing
    dy = 0.865 * hex_height        # vertical spacing

    minx, miny, maxx, maxy = usa_proj.total_bounds

    hexes = []
    row = 0
    y = miny - hex_height
    while y < maxy + hex_height:
        x_offset = (row % 2) * (dx / 2)
        x = minx - hex_width
        while x < maxx + hex_width:
            hexes.append(make_hex(x + x_offset, y, HEX_RADIUS_M))
            x += dx
        y += dy
        row += 1

    return gpd.GeoDataFrame(geometry=hexes, crs="EPSG:5070")


def assign_scores(hex_us_proj):
    """Add synthetic datacenter score attributes to the projected hex grid."""
    rng = np.random.default_rng(0)
    hex_us_proj["price_raw"] = rng.normal(40, 10, len(hex_us_proj))
    hex_us_proj["load_raw"] = rng.normal(200, 80, len(hex_us_proj))
    hex_us_proj["temp_raw"] = rng.normal(60, 10, len(hex_us_proj))
    hex_us_proj["renew_raw"] = rng.uniform(0, 1, len(hex_us_proj))
    hex_us_proj["stability_raw"] = rng.uniform(0.7, 1.0, len(hex_us_proj))
    hex_us_proj["co2_raw"] = rng.uniform(200, 800, len(hex_us_proj))

    for col in [
        "price_raw",
        "load_raw",
        "temp_raw",
        "renew_raw",
        "stability_raw",
        "co2_raw",
    ]:
        hex_us_proj[f"n_{col}"] = (hex_us_proj[col] - hex_us_proj[col].min()) / (
            hex_us_proj[col].max() - hex_us_proj[col].min()
        )

    hex_us_proj["profit"] = (
        0.40 * (1 - hex_us_proj["n_price_raw"])
        + 0.35 * (hex_us_proj["n_load_raw"])
        + 0.25 * (1 - hex_us_proj["n_temp_raw"])
    )

    hex_us_proj["sustain"] = (
        0.45 * (hex_us_proj["n_renew_raw"])
        + 0.35 * (hex_us_proj["n_stability_raw"])
        + 0.20 * (1 - hex_us_proj["n_co2_raw"])
    )

    hex_us_proj["dc_score_raw"] = (
        0.6 * hex_us_proj["profit"] + 0.4 * hex_us_proj["sustain"]
    )

    smoothing_note = None
    try:
        from sklearn.neighbors import NearestNeighbors

        centers = np.vstack(hex_us_proj.geometry.centroid.apply(lambda p: (p.x, p.y)))
        nbrs = NearestNeighbors(n_neighbors=7).fit(centers)
        _, idx = nbrs.kneighbors(centers)
        smooth = np.array(
            [hex_us_proj["dc_score_raw"].values[i].mean() for i in idx]
        )
        hex_us_proj["dc_score"] = smooth
    except Exception as exc:  # keep map working if sklearn is missing
        smoothing_note = (
            "Neighbor smoothing skipped because scikit-learn is unavailable. "
            "Install scikit-learn to match the notebook output exactly."
        )
        hex_us_proj["dc_score"] = hex_us_proj["dc_score_raw"]

    return hex_us_proj, smoothing_note


@st.cache_resource(show_spinner=True)
def load_hex_conus():
    """Load and score the hex grid, then clip to the continental US box."""
    usa = gpd.read_file(USA_URL)
    usa_border = usa.unary_union
    usa_gdf = gpd.GeoDataFrame(geometry=[usa_border], crs="EPSG:4326")

    usa_proj = usa_gdf.to_crs("EPSG:5070")  # NAD83 / Conus Albers
    hexgrid_proj = build_hexgrid(usa_proj)
    hex_us_proj = gpd.overlay(hexgrid_proj, usa_proj, how="intersection")

    hex_us_proj, smoothing_note = assign_scores(hex_us_proj)
    hex_us = hex_us_proj.to_crs("EPSG:4326")

    hex_conus = hex_us.cx[MIN_LON:MAX_LON, MIN_LAT:MAX_LAT]
    return hex_conus, smoothing_note


def render_map(hex_conus):
    """Create a folium map from the clipped hex grid (no geopandas.explore dependency)."""
    lat_center = (MIN_LAT + MAX_LAT) / 2
    lon_center = (MIN_LON + MAX_LON) / 2

    score_min, score_max = (
        float(hex_conus["dc_score"].min()),
        float(hex_conus["dc_score"].max()),
    )
    colormap = linear.BuGn_09.scale(score_min, score_max)
    colormap.caption = "Datacenter score"

    m = folium.Map(
        location=[lat_center, lon_center],
        zoom_start=4,
        tiles="CartoDB positron",
        zoom_control=True,
        scrollWheelZoom=False,
    )

    folium.GeoJson(
        hex_conus.__geo_interface__,
        style_function=lambda feature: {
            "fillColor": colormap(feature["properties"]["dc_score"]),
            "color": "#111",
            "weight": 0.4,
            "fillOpacity": 0.9,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["dc_score"],
            aliases=["Score:"],
            localize=True,
            sticky=True,
        ),
    ).add_to(m)

    colormap.add_to(m)
    html(m._repr_html_(), height=720)


def main():
    st.set_page_config(page_title="GridCast — Datacenter Score Map", layout="wide")
    st.title("⚡ GridCast — Datacenter Score Map")
    st.caption("Continental US hex map reproduced from datacenter_score.ipynb")

    with st.spinner("Building hex grid and computing scores..."):
        hex_conus, smoothing_note = load_hex_conus()

    render_map(hex_conus)

    st.markdown(
        f"""
**Bounding box:** {MIN_LAT}° to {MAX_LAT}° latitude, {MIN_LON}° to {MAX_LON}° longitude  
**Hex radius:** {HEX_RADIUS_M/1000:.0f} km (pointy-top)
"""
    )
    if smoothing_note:
        st.info(smoothing_note)


if __name__ == "__main__":
    main()
