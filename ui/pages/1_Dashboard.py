import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import streamlit as st
import json
import pandas as pd
import plotly.express as px
from agent.db import get_user_config
from agent.main import run_pipeline
from ui.style import apply_global_style

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
apply_global_style()

if "email" not in st.session_state or st.session_state.email is None:
    st.warning("Please log in on the main page first.")
    st.stop()

st.title("📊 Dashboard")

config = get_user_config(st.session_state.email)

if not config or not config.get("shopify_url"):
    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
    st.warning("⚠️ **Action Required:** Please go to the **Settings** page and enter your Shopify credentials to get started.")
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
    st.success("✅ Shopify credentials are connected.")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        source = st.selectbox("Select Data Source", ["shopify", "mock (testing)"])
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 Run Inventory Agent", type="primary", use_container_width=True):
            with st.spinner("Analyzing inventory and sending alerts..."):
                try:
                    actual_source = "shopify" if source == "shopify" else "mock"
                    summary = run_pipeline(user_config=config, source=actual_source, dry_run=False, force=False)
                    st.success(f"Run Complete! Critical: {summary['critical']}, Digest: {summary['digest']}")
                except Exception as e:
                    st.error(f"Pipeline failed: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<h3 style='margin-top: 2rem;'>📈 Historical Trends</h3>", unsafe_allow_html=True)
history_file = os.path.join("docs", "run_history.csv")

if not os.path.exists(history_file):
    st.info("No trend data available yet. Run the agent pipeline above.")
else:
    df = pd.read_csv(history_file)
    
    if not df.empty:
        # --- DATA CLEANING ---
        # Remove any Git conflict lines if they accidentally exist
        df = df[~df['date'].astype(str).str.contains('<<<|===|>>>', na=False)]
        
        # Convert date to a proper datetime object and sort
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date']).sort_values('date')
        
        # Format back to string for the chart
        df['date_str'] = df['date'].dt.strftime('%b %d, %H:%M')

        # Create a neon line chart
        fig = px.line(df, x="date_str", y=["critical", "digest"], 
                      color_discrete_sequence=["#00F0FF", "#FF0055"],
                      markers=True,
                      labels={"value": "Alerts", "variable": "Alert Type", "date_str": "Date"})
        
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E6EDF3", family="Lato"),
            legend_title_text="",
            xaxis=dict(
                showgrid=True, 
                gridcolor="#30363D",
                tickangle=45 # Angle the dates so they don't overlap
            ),
            yaxis=dict(showgrid=True, gridcolor="#30363D"),
            margin=dict(l=0, r=0, t=20, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Run history is empty.")

st.markdown("<h3 style='margin-top: 2rem;'>🚨 Current Alerts</h3>", unsafe_allow_html=True)
state_file = os.path.join("data", "state.json")

if os.path.exists(state_file):
    with open(state_file, "r") as f:
        state_data = json.load(f)
    if state_data:
        df_state = pd.DataFrame([
            {"SKU": sku, "Urgency": rec.get("urgency", "HEALTHY"), "Alerts (7d)": rec.get("alert_count_7d", 0), "Last Alerted": rec.get("last_alerted_at", "N/A")} 
            for sku, rec in state_data.items()
        ])
        st.dataframe(df_state, use_container_width=True, hide_index=True)