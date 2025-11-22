# ======================================================
# GridCast — U.S. Energy Demand Dashboard (Streamlit)
# ======================================================
import os
import requests
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import matplotlib.pyplot as plt
from statsmodels.tsa.statespace.sarimax import SARIMAX
from dotenv import load_dotenv
import os

load_dotenv()
EIA_API_KEY = os.getenv("EIA_API_KEY")


# ------------------------------------------------------
# Page setup
# ------------------------------------------------------
st.set_page_config(page_title="GridCast — U.S. Dashboard", layout="wide")
st.title("⚡ GridCast — U.S. Energy Demand Forecast Dashboard")

EIA_API_KEY = os.getenv("EIA_API_KEY")
if not EIA_API_KEY:
    st.error("Please set your EIA_API_KEY environment variable.")
    st.stop()

AGGREGATED_REGIONS = [
    "CAL","CAR","CENT","FLA","MIDA","MIDW","NE","NW","NY","SE","SW","TEN","TEX","US48"
]

region_to_states = {
    "CAL": ["California"],
    "CAR": ["North Carolina", "South Carolina"],
    "CENT": ["Arkansas", "Kansas", "Louisiana", "Missouri", "Nebraska", "Oklahoma"],
    "FLA": ["Florida"],
    "MIDA": ["Delaware","District of Columbia","Maryland","New Jersey","Pennsylvania","Virginia","West Virginia"],
    "MIDW": ["Illinois","Indiana","Iowa","Kentucky","Michigan","Minnesota","North Dakota","Ohio","South Dakota","Wisconsin"],
    "NE": ["Connecticut","Maine","Massachusetts","New Hampshire","Rhode Island","Vermont"],
    "NY": ["New York"],
    "NW": ["Idaho","Montana","Oregon","Washington","Wyoming"],
    "SE": ["Alabama","Georgia","Mississippi"],
    "SW": ["Arizona","Colorado","New Mexico","Nevada","Utah"],
    "TEN": ["Tennessee"],
    "TEX": ["Texas"],
}

GEO_URL = "https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json"
EIA_URL = "https://api.eia.gov/v2/electricity/rto/region-data/data/"

# ------------------------------------------------------
# Cached Data Fetch
# ------------------------------------------------------
@st.cache_data(show_spinner=True)
def load_eia_data():
    params = {
        "api_key": EIA_API_KEY,
        "frequency": "hourly",
        "data[0]": "value",
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "offset": 0,
        "length": 5000,
    }
    for r in AGGREGATED_REGIONS:
        params.setdefault("facets[respondent][]", []).append(r)

    try:
        resp = requests.get(EIA_URL, params=params)
        resp.raise_for_status()
        data = resp.json()["response"]["data"]
        df = pd.DataFrame(data)
        df.to_csv("eia_us_cached.csv", index=False)
    except Exception as exc:
        st.warning(f"⚠️ Using cached data because API failed: {exc}")
        df = pd.read_csv("eia_us_cached.csv")

    df["datetime"] = pd.to_datetime(df["period"])
    df["demand_MW"] = pd.to_numeric(df["value"], errors="coerce")
    df["region"] = df["respondent"]
    return df

df = load_eia_data()
latest_time = df["datetime"].max()

# ------------------------------------------------------
# Forecasting Helper
# ------------------------------------------------------
def forecast_region(df_region, horizon=24):
    """Forecast next-day electricity demand for a given region."""
    s = (df_region.drop_duplicates(subset=["datetime"])
                  .set_index("datetime")["demand_MW"]
                  .asfreq("h")
                  .interpolate("time"))
    if s.empty:
        return pd.Series([], dtype=float)

    s_scaled = s / 1000.0
    model = SARIMAX(s_scaled, order=(2,0,2), seasonal_order=(1,1,1,24),
                    trend='c', enforce_stationarity=False, enforce_invertibility=False)
    fit = model.fit(disp=False)
    yhat = fit.get_forecast(steps=horizon).predicted_mean * 1000.0

    if len(yhat) > 0:
        offset = float(s.iloc[-1] - yhat.iloc[0])
        yhat = yhat + offset
    return yhat.clip(0)

# ------------------------------------------------------
# Generate next-day forecasts for all regions
# ------------------------------------------------------
st.sidebar.header("⚙️ Settings")
forecast_horizon = st.sidebar.slider("Forecast horizon (hours)", 6, 48, 24)
refresh = st.sidebar.button("🔄 Refresh data")

if refresh:
    load_eia_data.clear()
    st.rerun()

st.info(f"Latest data timestamp: {latest_time:%Y-%m-%d %H:%M}")

forecasts = []
for region, group in df.groupby("region"):
    yhat = forecast_region(group, horizon=forecast_horizon)
    if not yhat.empty:
        forecasts.append(pd.DataFrame({
            "region": region,
            "datetime": yhat.index,
            "forecast_MW": yhat.values
        }))
forecast_df = pd.concat(forecasts, ignore_index=True)

# ------------------------------------------------------
# Latest snapshot for map
# ------------------------------------------------------
latest_idx = df.groupby("region")["datetime"].idxmax()
latest_df = df.loc[latest_idx, ["region", "demand_MW", "datetime"]].copy()
latest_df = latest_df[latest_df["region"].isin(region_to_states.keys())]
latest_df["state"] = latest_df["region"].map(lambda x: region_to_states[x][0])

# ------------------------------------------------------
# Map visualization
# ------------------------------------------------------
st.subheader("🗺️ U.S. Electricity Demand Map (Latest Hour)")
import folium
from streamlit_folium import st_folium

# ======================================================
# 3️⃣ Choropleth via Folium (OpenStreetMap)
# ======================================================
geo_url = "https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json"

m = folium.Map(location=[39.5, -98.35], zoom_start=4, tiles="CartoDB positron")

choropleth = folium.Choropleth(
    geo_data=geo_url,
    name="Electricity Demand (MW)",
    data=latest_df,  # your demand dataframe
    columns=["state", "demand_MW"],
    key_on="feature.properties.name",
    fill_color="YlOrRd",
    fill_opacity=0.8,
    line_opacity=0.3,
    nan_fill_color="gray",
    legend_name=f"Electricity Demand (MW) — {latest_time:%Y-%m-%d %H:%M}",
).add_to(m)

# ✅ Tooltip must attach to a GeoJson object, not the map
folium.GeoJson(
    geo_url,
    name="State Boundaries",
    tooltip=folium.GeoJsonTooltip(
        fields=["name"],
        aliases=["State:"],
        localize=True
    )
).add_to(m)

folium.LayerControl().add_to(m)

# ======================================================
# 4️⃣ Display map in Streamlit
# ======================================================
st.subheader("🗺️ U.S. Electricity Demand (Latest Hour)")
st_folium(m, width=1100, height=600)


# ------------------------------------------------------
# Regional forecast tabs
# ------------------------------------------------------
st.subheader("📈 Regional Forecasts")
tabs = st.tabs([r for r in region_to_states.keys()])

for tab, region in zip(tabs, region_to_states.keys()):
    with tab:
        region_df = df[df["region"] == region]
        actual = (
            region_df.drop_duplicates(subset=["datetime"])
            .set_index("datetime")["demand_MW"]
            .asfreq("h")
            .interpolate()
        )
        forecast = (
            forecast_df[forecast_df["region"] == region]
            .drop_duplicates(subset=["datetime"])
            .set_index("datetime")["forecast_MW"]
        )

        if len(actual) < 24:
            st.warning("Not enough data for this region yet.")
            continue

        fig, ax = plt.subplots(figsize=(8,3))
        ax.plot(actual[-7*24:], label="Actual (past week)", color="steelblue")
        ax.plot(forecast, label="Forecast (next day)", color="tomato", linestyle="--")
        ax.set_title(f"Electricity Demand Forecast — {region}")
        ax.set_xlabel("Datetime"); ax.set_ylabel("MW"); ax.legend()
        st.pyplot(fig)