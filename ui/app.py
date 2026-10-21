import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from agent.db import get_user_config, save_user_config

st.set_page_config(page_title="Inventory Agent", page_icon="📦", layout="wide")

# Initialize session state
if "email" not in st.session_state:
    st.session_state.email = None

st.title("📦 AI Inventory Agent")
st.markdown("Welcome to your automated e-commerce assistant.")

if st.session_state.email is None:
    st.subheader("Login / Sign Up")
    st.info("Enter your email to access your dashboard. If you are new, an account will be created automatically.")
    
    with st.form("login_form"):
        email = st.text_input("Email Address")
        submit = st.form_submit_button("Continue")
        
        if submit:
            if not email or "@" not in email:
                st.error("Please enter a valid email address.")
            else:
                user = get_user_config(email)
                if not user:
                    save_user_config(email, {
                        "shopify_url": "", "shopify_client_id": "", "shopify_client_secret": "",
                        "gmail_user": "", "gmail_app_password": "", "owner_email": "",
                        "discord_webhook_url": "", "discord_webhook_url_logs": ""
                    })
                    st.success("Account created!")
                
                st.session_state.email = email
                st.rerun()

else:
    st.success(f"Logged in as: {st.session_state.email}")
    st.markdown("### Welcome back!")
    st.markdown("👈 Use the sidebar to navigate to your **Dashboard** or **Settings**.")
    
    if st.button("Logout"):
        st.session_state.email = None
        st.rerun()