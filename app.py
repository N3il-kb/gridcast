# ======================================================
# U.S. EnergyCast (Streamlit Dashboard)
# ======================================================
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.statespace.sarimax import SARIMAX
import kagglehub
import os

DEMAND_KEYWORDS = ("mw", "mwh", "demand", "load", "consumption", "value")
REGION_KEYWORDS = ("region", "respondent", "ba", "balancing", "market", "name", "area", "state")


def _clean_demand_series(series: pd.Series) -> pd.Series:
    """Convert the raw demand column to numeric, handling commas and blanks."""
    cleaned = series.astype(str).str.strip()
    cleaned = cleaned.str.replace(",", "", regex=False)
    cleaned = cleaned.mask(cleaned.isin({"", "-", "nan", "none"}))
    return pd.to_numeric(cleaned, errors="coerce")


def _detect_region_column(df: pd.DataFrame, exclude: set[str]) -> str | None:
    """Find a categorical column that best represents the region/BA name."""
    ordered_cols = [
        col for col in df.columns
        if col not in exclude
    ]
    # Try keyword-based match first
    for keyword in REGION_KEYWORDS:
        for col in ordered_cols:
            if keyword not in col:
                continue
            if df[col].nunique(dropna=True) > 1:
                return col
    # Fallback: highest-cardinality object column
    obj_cols = [
        col for col in ordered_cols
        if df[col].dtype == object and df[col].nunique(dropna=True) > 1
    ]
    if obj_cols:
        return max(obj_cols, key=lambda c: df[c].nunique(dropna=True))
    return None

st.set_page_config(page_title="U.S. EnergyCast", layout="wide")

# ------------------------------------------------------
# 1️⃣ Load Dataset via KaggleHub
# ------------------------------------------------------
@st.cache_data
def load_data():
    def _resolve_dataset_path():
        """Prefer a user-supplied CSV via GRIDCAST_CSV before hitting Kaggle."""
        direct_path = os.environ.get("GRIDCAST_CSV")
        if direct_path:
            if not os.path.isfile(direct_path):
                raise FileNotFoundError(f"GRIDCAST_CSV points to {direct_path}, but no file exists.")
            return direct_path

        kaggle_path = kagglehub.dataset_download("antgoldbloom/us-eia-hourly-electricity-consumption")
        csv_files = [
            f for f in os.listdir(kaggle_path)
            if f.lower().endswith(".csv")
        ]
        if not csv_files:
            raise FileNotFoundError("No CSV files were found in the downloaded Kaggle dataset.")
        # Prefer the largest CSV (heuristic for the main data file)
        csv_files.sort(key=lambda f: os.path.getsize(os.path.join(kaggle_path, f)), reverse=True)
        return os.path.join(kaggle_path, csv_files[0])

    def _detect_datetime_column(df: pd.DataFrame) -> str:
        """Find a datetime-like column by trying the most likely textual matches first."""
        keyword_order = ("datetime", "timestamp", "time", "date", "hour_ending", "hour")
        ignore_tokens = ("timezone", "tz")
        candidates = [
            col for col in df.columns
            if any(k in col for k in keyword_order)
            and not any(bad in col for bad in ignore_tokens)
        ]
        if not candidates:
            candidates = list(df.columns)

        best_col = None
        best_valid = 0
        for col in candidates:
            if pd.api.types.is_numeric_dtype(df[col]):
                continue
            converted = pd.to_datetime(df[col], errors="coerce")
            valid = converted.notna().sum()
            if valid > best_valid:
                best_col = col
                best_valid = valid
                df[col] = converted
        if best_col is None or best_valid == 0:
            raise ValueError("Could not find a datetime column in the dataset.")
        return best_col

    try:
        dataset_path = _resolve_dataset_path()
    except Exception as exc:
        st.error(
            "Unable to locate the dataset. Set GRIDCAST_CSV to a local CSV file "
            "or configure Kaggle credentials. "
            f"Details: {exc}"
        )
        st.stop()

    df = pd.read_csv(dataset_path)
    df.columns = [c.lower().strip() for c in df.columns]
    try:
        time_col = _detect_datetime_column(df)
    except ValueError as exc:
        st.error(str(exc))
        st.stop()

    demand_candidates = []
    for col in df.columns:
        if col == time_col:
            continue
        cleaned = _clean_demand_series(df[col])
        numeric_count = cleaned.notna().sum()
        if numeric_count == 0:
            continue
        ratio = numeric_count / len(cleaned)
        unique_vals = cleaned.nunique()
        has_keyword = any(keyword in col for keyword in DEMAND_KEYWORDS)
        if has_keyword or (ratio >= 0.9 and unique_vals >= 50):
            df[col] = cleaned
            demand_candidates.append(col)

    if not demand_candidates:
        st.error(
            "No numeric demand columns were found in the dataset. "
            "Ensure the CSV includes hourly demand fields (e.g. MW or MWh)."
        )
        st.stop()

    if len(demand_candidates) > 1:
        # Wide format: melt the numeric columns into a region field
        df_long = df[[time_col] + demand_candidates].melt(
            id_vars=[time_col], var_name="region", value_name="demand_MW"
        )
    else:
        # Long format: identify a region column to pair with the single demand column
        demand_col = demand_candidates[0]
        region_col = _detect_region_column(df, exclude={time_col, demand_col})
        if not region_col:
            df["region"] = "U.S. Total"
            region_col = "region"
        df_long = df[[time_col, region_col, demand_col]].rename(
            columns={region_col: "region", demand_col: "demand_MW"}
        )

    # Clean + sort
    df_long = df_long.rename(columns={time_col: "datetime"})
    df_long = df_long.dropna(subset=["demand_MW"]).sort_values("datetime")
    if df_long.empty:
        st.error(
            "All detected demand values are empty after cleaning. "
            "Double-check the source dataset."
        )
        st.stop()

    return df_long


# ✅ Load data once here
df = load_data()

# ------------------------------------------------------
# 2️⃣ Sidebar controls
# ------------------------------------------------------
st.sidebar.header("⚙️ Settings")

regions = sorted(df["region"].unique().tolist())
if not regions:
    st.error("No regions with numeric demand values were found.")
    st.stop()
selected_region = st.sidebar.selectbox("Select Region", regions, index=0)

forecast_days = st.sidebar.slider("Forecast horizon (days)", 7, 60, 30)

# ------------------------------------------------------
# 3️⃣ Prepare region series
# ------------------------------------------------------
region_df = df[df["region"] == selected_region].copy()

# Ensure datetime is parsed correctly
region_df["datetime"] = pd.to_datetime(region_df["datetime"], errors="coerce")
region_df = region_df.dropna(subset=["datetime"])

# Force numeric conversion of demand column
region_df["demand_MW"] = _clean_demand_series(region_df["demand_MW"])

# Aggregate hourly → daily mean (MWh)
region_df = (
    region_df
    .set_index("datetime")
    .resample("D")["demand_MW"]
    .mean()
    .dropna()
)
region_df.name = "demand_MW"

if region_df.empty:
    st.error("No demand data is available for the selected region.")
    st.stop()

# ------------------------------------------------------
# 4️⃣ Train SARIMA model
# ------------------------------------------------------
@st.cache_data
def train_model(series):
    model = SARIMAX(series, order=(2,1,2), seasonal_order=(1,1,1,7),
                    enforce_stationarity=False, enforce_invertibility=False)
    fit = model.fit(disp=False)
    return fit

fit = train_model(region_df)
forecast = fit.get_forecast(steps=forecast_days)
forecast_index = pd.date_range(region_df.index[-1] + pd.Timedelta(days=1),
                               periods=forecast_days, freq="D")
forecast_mean = forecast.predicted_mean
forecast_df = pd.DataFrame({"date": forecast_index, "forecast_MWh": forecast_mean.values})

# ------------------------------------------------------
# 5️⃣ Time series chart
# ------------------------------------------------------
st.subheader(f"🔮 {selected_region} Energy Demand Forecast")
fig, ax = plt.subplots(figsize=(10,4))
lookback = min(len(region_df), 180)
recent_history = region_df.iloc[-lookback:]  # use position-based slicing for datetime index
ax.plot(recent_history.index, recent_history, label="Historical", color="steelblue")
ax.plot(forecast_index, forecast_mean, label="SARIMA Forecast", color="tomato")
ax.set_title(f"{selected_region} Electricity Demand Forecast ({forecast_days} Days Ahead)")
ax.set_xlabel("Date"); ax.set_ylabel("MWh"); ax.legend()
st.pyplot(fig)

# ------------------------------------------------------
# 6️⃣ Summary metrics
# ------------------------------------------------------
avg_forecast = forecast_df["forecast_MWh"].mean()
peak_forecast = forecast_df["forecast_MWh"].max()
st.metric("Average Forecasted Demand (MWh)", f"{avg_forecast:,.0f}")
st.metric("Peak Forecasted Demand (MWh)", f"{peak_forecast:,.0f}")

# ------------------------------------------------------
# 7️⃣ Explanation text
# ------------------------------------------------------
st.markdown(f"""
### 📘 About This Dashboard
This dashboard forecasts short-term **electricity consumption** in U.S. regions using a **Seasonal ARIMA (SARIMA)** model trained on historical hourly data from the U.S. Energy Information Administration.

**Interpretation**
- The time-series plot shows daily average MWh demand extended *{forecast_days} days* into the future.
- Select any EIA region (e.g. CAL, TEX, MIDA) in the sidebar to view its forecast.

**Data source:** [US EIA Hourly Electricity Consumption (Kaggle)](https://www.kaggle.com/datasets/antgoldbloom/us-eia-hourly-electricity-consumption)
""")
