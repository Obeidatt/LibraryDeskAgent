import streamlit as st
from library_agent import run_agent
from chat_storage import (
    get_next_session_id,
    list_sessions,
    load_messages,
    save_message,
)

st.set_page_config(
    page_title="Library Desk Agent",
    page_icon="📚",
    layout="wide",
)

st.title("📚 Library Desk Agent")
st.caption("Local chat UI using Ollama + LangChain + SQLite")

# ====== Sidebar: Sessions ======
st.sidebar.header("Sessions")

# Load sessions from DB
sessions = list_sessions()  # [{session_id, started_at, updated_at}, ...]

session_labels = [
    f"Session {s['session_id']} (last: {s['updated_at']})" for s in sessions
]
session_ids = [s["session_id"] for s in sessions]

options = ["➕ New session"] + session_labels
choice = st.sidebar.selectbox("Choose session", options)

new_clicked = st.sidebar.button("Start new session")

if "session_id" not in st.session_state:
    st.session_state["session_id"] = None


if new_clicked or st.session_state["session_id"] is None:
     
    st.session_state["session_id"] = get_next_session_id()
    st.session_state["messages"] = []
else:
    if choice != "➕ New session":
        idx = options.index(choice) - 1  
        selected_session_id = session_ids[idx]

        if st.session_state["session_id"] != selected_session_id:
            st.session_state["session_id"] = selected_session_id
            
            st.session_state["messages"] = load_messages(selected_session_id)

current_session_id = st.session_state["session_id"]
st.sidebar.markdown(f"**Current session:** `{current_session_id}`")

 
if "messages" not in st.session_state:
    st.session_state["messages"] = []

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

 
user_input = st.chat_input("Ask Us Here....")

if user_input:
     
    with st.chat_message("user"):
        st.markdown(user_input)

     
    save_message(current_session_id, "user", user_input)
    st.session_state["messages"].append({"role": "user", "content": user_input})

     
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                reply = run_agent(user_input, session_id=current_session_id)
            except Exception as e:
                reply = f"Error when excute the prompt:\n\n`{e}`"

            st.markdown(reply)

  
    save_message(current_session_id, "assistant", reply)
    st.session_state["messages"].append({"role": "assistant", "content": reply})
