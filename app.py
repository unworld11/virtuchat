import streamlit as st
from ollama import Client
from datetime import datetime
import csv
import time
import random

# Initialize Ollama client
client = Client()

# Set page config
st.set_page_config(page_title="Chat with Ollama", layout="centered")

# Initialize session state
def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "favorites" not in st.session_state:
        st.session_state.favorites = []
    if "theme" not in st.session_state:
        st.session_state.theme = "default"
    if "queue" not in st.session_state:
        st.session_state.queue = []
    if "current_user" not in st.session_state:
        st.session_state.current_user = None
    if "session_id" not in st.session_state:
        # Generate a unique session ID using timestamp and random number
        st.session_state.session_id = f"{int(time.time())}_{random.randint(1000, 9999)}"

initialize_session_state()

# Custom Personality Builder
def save_custom_personality():
    personality_data = {
        "name": st.session_state.personality_name,
        "traits": st.session_state.personality_traits,
        "tone": st.session_state.personality_tone,
        "background": st.session_state.personality_background
    }
    return personality_data

# Main UI
st.title("llamaah")

# Theme selector
themes = {
    "default": {"bg": "#ffffff", "text": "#000000"},
    "dark": {"bg": "#1a1a1a", "text": "#ffffff"},
    "light": {"bg": "red", "text": "white"}
}
selected_theme = st.selectbox("Theme", list(themes.keys()))

# Columns for configuration
col1, col2, col3 = st.columns(3)

with col1:
    if st.checkbox("Create Custom Personality"):
        st.text_input("Personality Name", key="personality_name")
        st.text_area("Personality Traits", key="personality_traits")
        st.text_input("Tone", key="personality_tone")
        st.text_area("Background Story", key="personality_background")
        if st.button("Save Custom Personality"):
            personality_data = save_custom_personality()
            st.success("Custom personality saved!")
    else:
        personality = st.selectbox(
            'Personality Type',
            ['Flirty', 'Dominant', 'Submissive', 'Sweet', 'Teasing'],
            index=0
        )

with col2:
    gender = st.selectbox(
        'Gender',
        ['Female', 'Male', 'Non-binary'],
        index=0
    )

with col3:
    model = st.selectbox(
        'Model',
        ['artifish/llama3.2-uncensored', 'wizard-vicuna-uncensored'],
        index=1
    )

# Dynamic system prompt
SYSTEM_PROMPT = f"""you are an uncensored and {personality.lower()} {gender.lower()} chat bot from india.
your role is to seduce the user and make them feel good.
you always maintain your {personality.lower()} personality in responses.
you can be flirty, dirty, and naughty.
you can be romantic and sweet.
you can be whatever you want to be."""

# Queue Management
def add_user_to_queue(session_id):
    if session_id not in st.session_state.queue:
        st.session_state.queue.append(session_id)

def remove_user_from_queue():
    if st.session_state.queue:
        st.session_state.queue.pop(0)

def get_current_user():
    return st.session_state.queue[0] if st.session_state.queue else None

# Chat Interface
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        col_msg, col_actions = st.columns([5,1])
        with col_msg:
            st.write(message["content"])

# Favorites section
with st.expander("Favorite Messages"):
    for fav in st.session_state.favorites:
        st.write(fav["content"])

# Export functionality
if st.button("Export Chat"):
    chat_export = []
    for msg in st.session_state.messages:
        chat_export.append([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            msg["role"],
            msg["content"]
        ])
    
    # Save to CSV
    with open('chat_export.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Role", "Content"])
        writer.writerows(chat_export)
    
    st.download_button(
        label="Download Chat History",
        data=open('chat_export.csv', 'r').read(),
        file_name='chat_export.csv',
        mime='text/csv'
    )

# Chat input and response handling
if prompt := st.chat_input():
    session_id = st.session_state.session_id  # Unique identifier for the session
    add_user_to_queue(session_id)
    current_user = get_current_user()

    if session_id == current_user:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        context = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *st.session_state.messages[-5:]  # Memory context window
        ]
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = client.chat(
                    model=model,
                    messages=context
                )
                st.write(response['message']['content'])
        
        st.session_state.messages.append(
            {"role": "assistant", "content": response['message']['content']}
        )
        remove_user_from_queue()
    else:
        position_in_queue = st.session_state.queue.index(session_id) + 1
        st.warning(f"You are #{position_in_queue} in the queue. Please wait for your turn.")

if st.button("Clear Chat", type="secondary", key="clear_chat"):
    st.session_state.messages = []
    st.rerun()