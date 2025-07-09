import streamlit as st
from langchain_core.messages import HumanMessage, SystemMessage
from agent import app  # Your LangGraph agent
import os

st.set_page_config(page_title="SmartCare Bot", layout="wide")
st.title("🏥 SmartCare Bot")

# Session state to persist chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    role = "user" if isinstance(msg, HumanMessage) else "assistant"
    st.chat_message(role).markdown(msg.content)

# User input
if prompt := st.chat_input("Ask about appointments, doctors, or availability..."):
    # Show user message
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append(HumanMessage(content=prompt))

    # Get response from LangGraph agent
    with st.spinner("Thinking..."):
        for event in app.stream(
            {"messages": [SystemMessage(content="You are a helpful assistant."), st.session_state.messages[-1]]},
            config={"configurable": {"thread_id": 42}},
        ):
            if event.get("agent", ""):
                output_msg = event["agent"]["messages"][-1]
                st.chat_message("assistant").markdown(output_msg.content)
                st.session_state.messages.append(output_msg)

# 🚨 Stop App Button
st.divider()
st.markdown("## ⚙️ Streamlite Option")
if st.button("🔴 Stop SmartCare Bot"):
    st.warning("Shutting down the app...")
    os._exit(0) 
