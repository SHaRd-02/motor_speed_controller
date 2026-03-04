import streamlit as st
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import pandas as pd

from streamlit_autorefresh import st_autorefresh

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Auto refresh every 2 seconds (2000 ms)
st_autorefresh(interval=2000, key="realtime_refresh")


# Realtime-optimized function to retrieve historical speed data
def get_historical_data():
    try:
        response = supabase.table("speed_data") \
            .select("*") \
            .order("id", desc=True) \
            .limit(100) \
            .execute()

        data = response.data

        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)

        # Ensure speed column is numeric
        if "speed" in df.columns:
            df["speed"] = pd.to_numeric(df["speed"], errors="coerce")

        # Drop rows where speed is NaN
        df = df.dropna(subset=["speed"])

        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values("timestamp")
        elif "id" in df.columns:
            df = df.sort_values("id")

        # Reset index to ensure clean plotting
        df = df.reset_index(drop=True)

        return df

    except Exception as e:
        st.error(f"Supabase error: {e}")
        return pd.DataFrame()

# Streamlit dashboard layout
st.title("DC Motor Speed Dashboard")
st.subheader("Real-time Speed Visualization")

# Retrieve and display historical data
data = get_historical_data()
if not data.empty and "speed" in data.columns:
    st.line_chart(data[["speed"]])
else:
    st.warning("No valid numeric speed data available.")
