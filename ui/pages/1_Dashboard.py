import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import streamlit as st
import json
from agent.db import get_user_config
from agent.main import run_pipeline

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

if "email" not in st.session_state or st.session_state.email is None:
    st.warning("Please log in on the main page first.")
    st.stop()

st.title("📊 Inventory Dashboard")
st.markdown(f"Logged in as: **{st.session_state.email}**")

# Fetch the user's config from Supabase
config = get_user_config(st.session_state.email)

if not config or not config.get("shopify_url"):
    st.warning("⚠️ Please go to the **Settings** page and enter your Shopify credentials first.")
else:
    st.success("✅ Shopify credentials found.")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        source = st.selectbox("Data Source", ["shopify", "mock"])
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 Run Agent Pipeline Now", type="primary", use_container_width=True):
            with st.spinner("Running pipeline... This may take 10-20 seconds."):
                try:
                    summary = run_pipeline(user_config=config, source=source, dry_run=False, force=False)
                    st.success(f"Run Complete! Critical: {summary['critical']}, Digest: {summary['digest']}")
                except Exception as e:
                    st.error(f"Pipeline failed: {e}")

st.divider()
st.subheader("Recent Alerts (Local State)")
state_file = os.path.join("data", "state.json")

if not os.path.exists(state_file):
    st.info("No inventory data found yet. Run the agent pipeline above.")
else:
    with open(state_file, "r") as f:
        state_data = json.load(f)
        
    if not state_data:
        st.info("State file is empty. No alerts triggered recently.")
    else:
        table_data = [{"SKU": sku, "Urgency": rec.get("urgency", "HEALTHY"), "Alerts (7d)": rec.get("alert_count_7d", 0), "Last Alerted": rec.get("last_alerted_at", "N/A")} for sku, rec in state_data.items()]
        st.dataframe(table_data, use_container_width=True)