import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import streamlit as st
from agent.rag import ask_inventory, rebuild_vector_store
from ui.style import apply_global_style

st.set_page_config(page_title="AI Chatbot", page_icon="🤖", layout="wide")
apply_global_style()

if "email" not in st.session_state or st.session_state.email is None:
    st.warning("Please log in on the main page first.")
    st.stop()

st.title("🤖 AI Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "vectorstore" not in st.session_state:
    with st.spinner("Loading AI memory..."):
        st.session_state.vectorstore = rebuild_vector_store()

with st.sidebar:
    st.markdown("### ⚙️ System")
    if st.button("🔄 Sync Knowledge Base", use_container_width=True):
        with st.spinner("Updating AI memory..."):
            st.session_state.vectorstore = rebuild_vector_store()
            if st.session_state.vectorstore:
                st.success("Memory updated!")
            else:
                st.error("No data found to embed.")
    
    st.divider()
    st.markdown("### 💡 Suggested Prompts")
    
    def handle_prompt(prompt_text):
        st.session_state.messages.append({"role": "user", "content": prompt_text})
        st.session_state.messages.append({"role": "assistant", "content": "Thinking..."})
        st.rerun()

    if st.button("How is my inventory right now?", use_container_width=True):
        handle_prompt("How is my inventory right now?")
    if st.button("Which stock do I pre-order?", use_container_width=True):
        handle_prompt("Which stock do I pre-order?")
    if st.button("What are the chances of stock being dead?", use_container_width=True):
        handle_prompt("What are the chances of stock being dead?")

# --- CHAT INTERFACE ---
# Display chat history
for message in st.session_state.messages:
    # We removed the avatar parameter completely. 
    # Streamlit's default avatars work perfectly with our CSS.
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Check if the last message is a "Thinking..." placeholder
if st.session_state.messages and st.session_state.messages[-1]["content"] == "Thinking...":
    # Generate real response
    prompt = st.session_state.messages[-2]["content"]
    response = ask_inventory(prompt, st.session_state.vectorstore)
    
    # Replace placeholder with actual response
    st.session_state.messages[-1]["content"] = response
    st.rerun()

# Accept new input
if prompt := st.chat_input("iMessage"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append({"role": "assistant", "content": "Thinking..."})
    st.rerun()