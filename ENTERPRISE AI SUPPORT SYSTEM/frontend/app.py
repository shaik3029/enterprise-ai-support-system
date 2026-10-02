import streamlit as st
import os
import sys

# Ensure backend and database imports work smoothly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.agents import handle_user_query

st.set_page_config(page_title="Enterprise Support AI", page_icon="🤖", layout="wide")

st.title("🤖 Multi-Agent Enterprise AI Support Platform")
st.markdown("Automated Routing across **Database**, **Policy RAG**, and **Ticketing Systems**.")

# Sidebar - Configuration
st.sidebar.header("🔑 Authentication & User Profile")
groq_api_key = st.sidebar.text_input("Enter Groq API Key:", type="password")
user_id = st.sidebar.text_input("User ID:", value="USR101")

st.sidebar.markdown("---")
st.sidebar.subheader("Quick Test Profiles")
st.sidebar.code("USR101 - Alex Johnson (Enterprise)")
st.sidebar.code("USR102 - Sam Lee (Overdue)")
st.sidebar.code("USR103 - SBI Customer (Savings)")

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat Messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input & Routing Execution
if query := st.chat_input("Ask a question about your account, policies, or report an issue..."):
    if not groq_api_key:
        st.error("Please enter your Groq API Key in the sidebar to proceed.")
    else:
        # User message
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)

        # Assistant thinking & Multi-Agent Execution
        with st.chat_message("assistant"):
            with st.spinner("Routing request across Enterprise Agents..."):
                result = handle_user_query(user_id, query, groq_api_key)
                
                agent_used = result["agent"]
                response_text = result["response"]
                
                formatted_response = f"**[{agent_used}]**\n\n{response_text}"
                st.markdown(formatted_response)
                
                st.session_state.messages.append({"role": "assistant", "content": formatted_response})