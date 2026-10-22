import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from agent.db import get_user_config, save_user_config
from ui.style import apply_global_style

st.set_page_config(page_title="Inventory Agent", page_icon="📦", layout="centered")
apply_global_style()

if "email" not in st.session_state:
    st.session_state.email = None

if st.session_state.email is None:
    st.markdown("<h1 style='text-align: center; margin-top: 3rem; font-size: 3rem;'>📦 AI Inventory</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94A3B8; font-size: 1.1rem; margin-bottom: 2rem;'>Automated inventory monitoring powered by AI.</p>", unsafe_allow_html=True)
    
    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
    st.markdown("<h3 style='margin-top: 0;'>Welcome Back</h3>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 0.9rem;'>Enter your email to log in or create an account.</p>", unsafe_allow_html=True)
    
    with st.form("login_form"):
        email = st.text_input("Email Address", placeholder="you@company.com")
        st.markdown("<br>", unsafe_allow_html=True)
        submit = st.form_submit_button("Continue to Dashboard")
        
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
                    st.success("Account created successfully!")
                
                st.session_state.email = email
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

else:
    # Premium Sidebar Account Info
    st.sidebar.markdown(f"""
    <div style='padding: 1rem; background: rgba(30, 41, 59, 0.5); border-radius: 10px; margin-bottom: 1rem;'>
        <p style='margin: 0; font-size: 0.8rem; color: #94A3B8;'>Logged in as</p>
        <p style='margin: 0; font-weight: 600; color: #F8FAFC;'>{st.session_state.email}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.sidebar.button("Logout"):
        st.session_state.email = None
        st.rerun()
        
    st.markdown("<h1 style='margin-bottom: 0;'>Welcome back! 👋</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94A3B8;'>Here is a quick overview of your workspace.</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
    st.markdown("### 🚀 Getting Started")
    st.markdown("""
    <ul style='color: #94A3B8; line-height: 1.8;'>
        <li>Go to <b>⚙️ Settings</b> to securely link Shopify, Email, and Discord.</li>
        <li>Go to <b>📊 Dashboard</b> to run your first inventory analysis.</li>
        <li>Go to <b>🤖 Chatbot</b> to ask AI questions about your data.</li>
    </ul>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)