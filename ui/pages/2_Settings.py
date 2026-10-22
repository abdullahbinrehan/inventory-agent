import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import streamlit as st
from agent.db import get_user_config, save_user_config
from ui.style import apply_global_style

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")
apply_global_style()

if "email" not in st.session_state or st.session_state.email is None:
    st.warning("Please log in on the main page first.")
    st.stop()

st.title("⚙️ Account Settings")
st.markdown("Connect your store and notification channels. All data is encrypted and stored securely.")

config = get_user_config(st.session_state.email) or {}

# Use tabs for clean organization
tab1, tab2, tab3 = st.tabs(["🛍️ Shopify Setup", "📧 Email Alerts", "💬 Discord Alerts"])

with tab1:
    st.subheader("Shopify Credentials")
    with st.expander("❓ How to get your Shopify API Credentials (Click to expand)"):
        st.markdown("""
        1. Go to your [Shopify Dev Dashboard](https://dev.shopify.com/dashboard) and log in.
        2. Click **Apps** → **Create app**.
        3. Name it `Inventory Agent`.
        4. Go to **Versions** → **Create a new version**.
        5. Under **Access scopes**, select: `read_inventory`, `read_orders`, `read_locations`, `read_products`.
        6. Click **Release**, then click **Install app** and install it on your store.
        7. Go to **Settings** → **API Credentials**.
        8. Copy the **Client ID** and **Client Secret**.
        9. Your store URL is just the name of your store followed by `.myshopify.com` (e.g., `my-store.myshopify.com`).
        """)
    
    col1, col2 = st.columns(2)
    with col1:
        shopify_url = st.text_input("Shopify Store URL", value=config.get("shopify_url", ""), placeholder="your-store.myshopify.com")
        shopify_client_id = st.text_input("Client ID", value=config.get("shopify_client_id", ""), type="password")
    with col2:
        shopify_client_secret = st.text_input("Client Secret", value=config.get("shopify_client_secret", ""), type="password")

with tab2:
    st.subheader("Email Notifications (Gmail)")
    with st.expander("❓ How to get a Gmail App Password (Click to expand)"):
        st.markdown("""
        1. Go to your Google Account -> **Security**.
        2. Make sure **2-Step Verification** is turned ON.
        3. Search for **App Passwords** in the search bar and click it.
        4. Type `Inventory Agent` as the app name and click **Create**.
        5. Copy the 16-character password (remove the spaces).
        """)
    
    col3, col4 = st.columns(2)
    with col3:
        gmail_user = st.text_input("Your Gmail Address", value=config.get("gmail_user", ""), placeholder="you@gmail.com")
        gmail_app_password = st.text_input("Gmail App Password", value=config.get("gmail_app_password", ""), type="password", placeholder="16 characters")
    with col4:
        owner_email = st.text_input("Where to send alerts?", value=config.get("owner_email", ""), placeholder="you@gmail.com")

with tab3:
    st.subheader("Discord Notifications")
    with st.expander("❓ How to create Discord Webhooks (Click to expand)"):
        st.markdown("""
        1. Open Discord and go to your server.
        2. Right-click the channel you want alerts in (e.g., `#alerts`) and click **Edit Channel**.
        3. Go to **Integrations** → **Webhooks** → **New Webhook**.
        4. Name it `Inventory Alerts` and click **Copy Webhook URL**.
        5. Repeat this for a `#logs` channel to get your Logs Webhook URL.
        """)
    
    discord_webhook_url = st.text_input("Alerts Webhook URL", value=config.get("discord_webhook_url", ""), type="password")
    discord_webhook_url_logs = st.text_input("Logs Webhook URL", value=config.get("discord_webhook_url_logs", ""), type="password")

st.divider()

if st.button("💾 Save All Credentials", type="primary", use_container_width=True):
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
        st.success("✅ Credentials saved successfully!")
        st.balloons()
    else:
        st.error("❌ Failed to save credentials. Check the database connection.")