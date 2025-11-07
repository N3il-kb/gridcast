# ======================================================
# California EnergyCast (Streamlit Dashboard)
# ======================================================
import streamlit as st
import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
from statsmodels.tsa.statespace.sarimax import SARIMAX
import kagglehub
import os

st.set_page_config(page_title="California EnergyCast", layout="wide")

# ------------------------------------------------------
# 1️⃣ Load Dataset via KaggleHub
# ------------------------------------------------------
@st.cache_data
def load_data():
    path = kagglehub.dataset_download("amineamllal/california-poc")
    for file in os.listdir(path):
        if file.endswith(".csv"):
            dataset_path = os.path.join(path, file)
            break
    df = pd.read_csv(dataset_path)
    df = df[["Time", "Electric_demand"]].rename(columns={"Time":"date", "Electric_demand":"consumption_MWh"})
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").set_index("date")
    df_daily = df.resample("D").mean().dropna()
    return df_daily

df_daily = load_data()

# ------------------------------------------------------
# 2️⃣ Sidebar controls
# ------------------------------------------------------
st.sidebar.header("⚙️ Settings")
forecast_days = st.sidebar.slider("Forecast horizon (days)", 7, 60, 30)
metric_type = st.sidebar.selectbox("Map metric", ["Average", "Total", "Peak"])

# ------------------------------------------------------
# 3️⃣ Train SARIMA model
# ------------------------------------------------------
@st.cache_data
def train_model(series):
    model = SARIMAX(series, order=(2,1,2), seasonal_order=(1,1,1,7),
                    enforce_stationarity=False, enforce_invertibility=False)
    fit = model.fit(disp=False)
    return fit

fit = train_model(df_daily["consumption_MWh"])
forecast = fit.get_forecast(steps=forecast_days)
forecast_index = pd.date_range(df_daily.index[-1] + pd.Timedelta(days=1), periods=forecast_days, freq="D")
forecast_mean = forecast.predicted_mean
forecast_df = pd.DataFrame({"date": forecast_index, "forecast_MWh": forecast_mean.values})

# ------------------------------------------------------
# 4️⃣ Time series chart
# ------------------------------------------------------
st.subheader("🔮 Energy Demand Forecast")
fig, ax = plt.subplots(figsize=(10,4))
ax.plot(df_daily.index[-180:], df_daily["consumption_MWh"][-180:], label="Historical", color="steelblue")
ax.plot(forecast_index, forecast_mean, label="SARIMA Forecast", color="tomato")
ax.set_title(f"California Energy Consumption Forecast ({forecast_days} Days Ahead)")
ax.set_xlabel("Date"); ax.set_ylabel("MWh"); ax.legend()
st.pyplot(fig)

# ------------------------------------------------------
# 5️⃣ County-level map
# ------------------------------------------------------
CA_GEOJSON = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/california-counties.geojson"
gdf = gpd.read_file(CA_GEOJSON)
gdf = gdf.rename(columns={"name":"county"})

# derive base forecast value
if metric_type == "Average":
    base_forecast = forecast_df["forecast_MWh"].mean()
elif metric_type == "Total":
    base_forecast = forecast_df["forecast_MWh"].sum()
else:  # Peak
    base_forecast = forecast_df["forecast_MWh"].max()

# add light random variation
rng = np.random.default_rng(42)
variation = rng.normal(0, 0.05, len(gdf))
gdf["forecast_MWh"] = base_forecast * (1 + variation)

# plot
st.subheader("🗺️ Forecasted Energy Demand by County")
st.caption(f"Metric displayed: **{metric_type} energy demand ({forecast_days}-day forecast)**")

fig2, ax2 = plt.subplots(figsize=(8,8))
gdf.plot(column="forecast_MWh", cmap="YlGnBu", linewidth=0.6,
         edgecolor="black", legend=True, ax=ax2)
ax2.set_title(f"Forecasted {metric_type} Energy Demand by County (Next {forecast_days} Days)")
ax2.axis("off")
st.pyplot(fig2)

# ------------------------------------------------------
# 6️⃣ Explanation text
# ------------------------------------------------------
st.markdown("""
### 📘 About This Dashboard
This app forecasts short-term electricity consumption in California using a **Seasonal ARIMA (SARIMA)** model trained on historical power demand data.

**Interpretation:**
- The time-series plot shows daily average MWh demand, extended into the next *N* days.
- The map visualizes the **predicted energy intensity** per county (synthetic spatial distribution).

**Data source:** [California POC (Kaggle)](https://www.kaggle.com/datasets/amineamllal/california-poc)
""")
