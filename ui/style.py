import streamlit as st

def apply_global_style():
    st.markdown("""
    <style>
    /* Import Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Lato:wght@400;700&display=swap');
    
    /* Base Typography */
    html, body, [class*="css"] {
        font-family: 'Lato', sans-serif;
    }
    
    h1, h2, h3 {
        font-family: 'Playfair Display', serif !important;
        color: #FFFFFF !important;
        letter-spacing: 0.5px;
    }
    
    .stApp {
        background-color: #0B0F19;
        color: #E6EDF3;
    }
    
    /* Hide default elements */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    
    /* --- DISCORD-STYLE SIDEBAR --- */
    [data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #1F2937;
    }
    
    [data-testid="stSidebarNav"] li a {
        color: #9CA3AF !important;
        font-family: 'Lato', sans-serif;
        font-weight: 700;
        padding: 0.75rem 1.5rem;
        margin: 0.25rem 1rem;
        border-radius: 6px;
        transition: all 0.2s ease;
    }
    [data-testid="stSidebarNav"] li a:hover {
        background-color: #1F2937;
        color: #F3F4F6 !important;
    }
    [data-testid="stSidebarNav"] li a[aria-current="page"] {
        background: linear-gradient(90deg, rgba(0, 240, 255, 0.1) 0%, transparent 100%);
        color: #00F0FF !important;
        border-left: 3px solid #00F0FF;
    }

    /* --- GLOWING NEON BUTTONS --- */
    .stButton>button {
        background: transparent;
        color: #00F0FF !important;
        border: 1px solid #00F0FF;
        border-radius: 8px;
        font-family: 'Lato', sans-serif;
        font-weight: 700;
        transition: all 0.3s ease;
        box-shadow: 0 0 10px rgba(0, 240, 255, 0.2);
        width: 100%;
    }
    .stButton>button:hover {
        background: rgba(0, 240, 255, 0.1);
        box-shadow: 0 0 20px rgba(0, 240, 255, 0.6);
        transform: translateY(-2px);
    }
    
    /* Primary Buttons (Run Agent) */
    .stButton>button[kind="primary"] {
        background: #00F0FF;
        color: #0B0F19 !important;
        box-shadow: 0 0 15px rgba(0, 240, 255, 0.4);
    }
    .stButton>button[kind="primary"]:hover {
        box-shadow: 0 0 25px rgba(0, 240, 255, 0.8);
    }
    
    /* --- CARDS --- */
    .premium-card {
        background: #161B22;
        border: 1px solid #30363D;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.4);
        margin-bottom: 20px;
    }
    
    /* --- IMESSAGE CHAT BUBBLES --- */
    [data-testid="stChatMessage"] {
        background-color: transparent !important;
        border: none !important;
        padding: 0 !important;
        margin-bottom: 1rem !important;
        display: flex;
        align-items: flex-start;
    }
    
    /* AI Message (Left, Gray) */
    [data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarAssistant"]) {
        flex-direction: row;
    }
    [data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarAssistant"]) .stMarkdown {
        background-color: #262629;
        color: #E6EDF3;
        border-radius: 18px 18px 18px 4px;
        padding: 14px 20px;
        max-width: 85%;
    }

    /* User Message (Right, Blue) */
    [data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) {
        flex-direction: row-reverse;
    }
    [data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) .stMarkdown {
        background-color: #0A84FF;
        color: #FFFFFF;
        border-radius: 18px 18px 4px 18px;
        padding: 14px 20px;
        max-width: 85%;
    }
    
    /* Hide avatars for a cleaner iMessage look */
    [data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"] {
        display: none;
    }
    
    /* Fix any markdown tables that slip through */
    .stMarkdown table {
        width: 100% !important;
        margin: 10px 0;
        border-collapse: collapse;
    }
    .stMarkdown th, .stMarkdown td {
        padding: 8px 12px;
        border: 1px solid #444;
        text-align: left;
    }

    /* Chat Input */
    [data-testid="stChatInput"] {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-radius: 20px;
    }
    </style>
    """, unsafe_allow_html=True)