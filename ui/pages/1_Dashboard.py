import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import streamlit as st
import json

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

if "email" not in st.session_state or st.session_state.email is None:
    st.warning("Please log in on the main page first.")
    st.stop()

st.title("📊 Inventory Dashboard")
st.markdown(f"Logged in as: **{st.session_state.email}**")

state_file = os.path.join("data", "state.json")

if not os.path.exists(state_file):
    st.info("No inventory data found yet. Run the agent pipeline first.")
else:
    with open(state_file, "r") as f:
        state_data = json.load(f)
        
    if not state_data:
        st.info("State file is empty. No alerts triggered recently.")
    else:
        table_data = []
        for sku, record in state_data.items():
            table_data.append({
                "SKU": sku,
                "Urgency": record.get("urgency", "HEALTHY"),
                "Alerts (7d)": record.get("alert_count_7d", 0),
                "Last Alerted": record.get("last_alerted_at", "N/A")
            })
            
        st.dataframe(table_data, use_container_width=True)