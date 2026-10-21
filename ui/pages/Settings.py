import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import streamlit as st
from agent.db import get_user_config, save_user_config

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")

if "email" not in st.session_state or st.session_state.email is None:
    st.warning("Please log in on the main page first.")
    st.stop()

st.title("⚙️ Account Settings")
st.markdown("Enter your Shopify credentials and notification channels below.")

config = get_user_config(st.session_state.email) or {}

with st.form("settings_form"):
    st.subheader("Shopify Integration")
    st.markdown("Follow the guide in the README to get these from your Shopify Dev Dashboard.")
    
    col1, col2 = st.columns(2)
    with col1:
        shopify_url = st.text_input("Shopify Store URL", value=config.get("shopify_url", ""), placeholder="your-store.myshopify.com")
        shopify_client_id = st.text_input("Client ID", value=config.get("shopify_client_id", ""), type="password")
    with col2:
        shopify_client_secret = st.text_input("Client Secret", value=config.get("shopify_client_secret", ""), type="password")
        st.markdown("<br>", unsafe_allow_html=True)
        st.info("These credentials are used to fetch your live inventory.")

    st.divider()
    
    st.subheader("Email Notifications (Gmail)")
    col3, col4 = st.columns(2)
    with col3:
        gmail_user = st.text_input("Gmail Address", value=config.get("gmail_user", ""))
        gmail_app_password = st.text_input("Gmail App Password (16 chars)", value=config.get("gmail_app_password", ""), type="password")
    with col4:
        owner_email = st.text_input("Owner Email (where to send alerts)", value=config.get("owner_email", ""))
        st.info("Use a Google App Password, not your regular password.")

    st.divider()

    st.subheader("Discord Notifications")
    discord_webhook_url = st.text_input("Alerts Webhook URL", value=config.get("discord_webhook_url", ""), type="password")
    discord_webhook_url_logs = st.text_input("Logs Webhook URL", value=config.get("discord_webhook_url_logs", ""), type="password")

    st.divider()

    submit = st.form_submit_button("💾 Save Credentials", type="primary")

    if submit:
        new_data = {
            "shopify_url": shopify_url,
            "shopify_client_id": shopify_client_id,
            "shopify_client_secret": shopify_client_secret,
            "gmail_user": gmail_user,
            "gmail_app_password": gmail_app_password,
            "owner_email": owner_email,
            "discord_webhook_url": discord_webhook_url,
            "discord_webhook_url_logs": discord_webhook_url_logs,
        }
        
        if save_user_config(st.session_state.email, new_data):
            st.success("✅ Credentials saved successfully to the database!")
            st.balloons()
        else:
            st.error("❌ Failed to save credentials. Check the database connection.")