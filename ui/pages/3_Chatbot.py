import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import streamlit as st
from agent.rag import ask_inventory, rebuild_vector_store

st.set_page_config(page_title="AI Chatbot", page_icon="🤖", layout="wide")

if "email" not in st.session_state or st.session_state.email is None:
    st.warning("Please log in on the main page first.")
    st.stop()

st.title("🤖 Inventory Chatbot")
st.markdown("Ask me anything about your inventory. I know your current stock and your history.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Button to rebuild the database
if st.sidebar.button("🔄 Rebuild Vector Database"):
    with st.spinner("Reading files and rebuilding embeddings..."):
        success = rebuild_vector_store()
        if success:
            st.sidebar.success("Database rebuilt!")
        else:
            st.sidebar.error("No data found to embed.")

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("E.g., How is my inventory right now?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = ask_inventory(prompt)
            st.markdown(response)
            
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})