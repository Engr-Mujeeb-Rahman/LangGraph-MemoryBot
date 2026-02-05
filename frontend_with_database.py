import streamlit as st
from backend_with_database import chatbot , retrieve_all_threads
from langchain_core.messages import HumanMessage , AIMessage
import uuid



st.markdown("""
<style>

/* ---------- GLOBAL ---------- */
html, body, [class*="css"] {
    font-family: 'Inter', 'Segoe UI', sans-serif;
}

body {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
}

/* Remove Streamlit padding */
.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
}

/* ---------- SIDEBAR ---------- */
section[data-testid="stSidebar"] {
    background: linear-gradient(135deg, #141e30, #243b55);
    backdrop-filter: blur(12px);
    border-right: 1px solid rgba(255,255,255,0.08);
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #f5f5f5;
    letter-spacing: 0.5px;
}

section[data-testid="stSidebar"] button {
    width: 100%;
    background: #dde004;
    color: #000;
    border: none;
    border-radius: 10px;
    padding: 0.6rem;
    margin-bottom: 0.4rem;
    font-weight: 600;
    transition: all 0.25s ease-in-out;
}

section[data-testid="stSidebar"] button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0,0,0,0.4);
}

/* ---------- CHAT AREA ---------- */
div[data-testid="stChatMessage"] {
    border-radius: 16px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.6rem;
    max-width: 80%;
}

/* USER MESSAGE */
div[data-testid="stChatMessage"][aria-label="user message"] {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    margin-left: auto;
    box-shadow: 0 8px 25px rgba(0,0,0,0.35);
}

/* ASSISTANT MESSAGE */
div[data-testid="stChatMessage"][aria-label="assistant message"] {
    background: rgba(255,255,255,0.08);
    color: #eaeaea;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 6px 18px rgba(0,0,0,0.3);
}

/* ---------- CHAT INPUT ---------- */
div[data-testid="stChatInput"] textarea {
    background: #FFFFFF;
    color: #000000;
    caret-color: #000000 !important; /* Cursor color */
    border-radius: 14px;
    border: 1px solid #babab1;
    padding: 0.8rem;
}

/* Placeholder color */
div[data-testid="stChatInput"] textarea::placeholder {
    color: #999;
}

/* ---------- SCROLLBAR ---------- */
::-webkit-scrollbar {
    width: 6px;
}
::-webkit-scrollbar-track {
    background: transparent;
}
::-webkit-scrollbar-thumb {
    background: rgba(255,255,255,0.25);
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)




st.markdown("""
<div style="
    background: linear-gradient(135deg, #141e30, #243b55);
    padding: 1rem 1.5rem;
    border-radius: 16px;
    margin-bottom: 1rem;
    box-shadow: 0 10px 30px rgba(0,0,0,0.4);
">
    <h2 style="margin:0; color:#fff;">🤖 LangGraph Chatbot</h2>
    <p style="margin:0; color:#bbb; font-size:0.9rem;">
        Persistent memory • Multi-threaded • AI-powered
    </p>
</div>
""", unsafe_allow_html=True)




# utility functions

def generate_thread_id():
    thread_id = str(uuid.uuid4())
    return thread_id


def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(thread_id)
    st.session_state['message_history'] = []


def add_thread(thread_id , title = "New Chat"):
    for t in st.session_state['chat_threads']:
        if t['id'] == thread_id:
            return
    st.session_state['chat_threads'].append({
        'id': thread_id,
        'title': title
    })

def load_conversation(thread_id):
    state = chatbot.get_state(config={'configurable' : {'thread_id' : thread_id}})

    # Check if messages key exists in state values, return empty list if not
    return state.values.get('messages' , [])




# Session Setup
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = retrieve_all_threads()



# add_thread(st.session_state['thread_id'])

if st.session_state['thread_id'] not in [t['id'] for t in st.session_state['chat_threads']]:
    add_thread(st.session_state['thread_id'])



# Sidebar UI 
st.sidebar.title("LangGraph Chatbot")

if st.sidebar.button('New Chat'):
    reset_chat()

st.sidebar.header("My Conversations")


for thread in st.session_state['chat_threads'][::-1]:
    if st.sidebar.button(thread['title'], key=str(thread['id'])):
        st.session_state['thread_id'] = thread['id']
        messages = load_conversation(thread['id'])

        temp_messages = []
        for msg in messages:
            role = 'user' if isinstance(msg, HumanMessage) else 'assistant'
            temp_messages.append({
                'role': role,
                'content': msg.content
            })

        st.session_state['message_history'] = temp_messages



# Main UI

# loading the conversation history
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])


user_input = st.chat_input("Type Here... ")

if user_input:

    # first add the message to message_history
    st.session_state['message_history'].append({'role' : 'user' , 'content' : user_input})
    with st.chat_message('user'):
        st.text(user_input)

    # Set conversation title from first user message
    current_thread = next(
        t for t in st.session_state['chat_threads']
        if t['id'] == st.session_state['thread_id']
        )

    if current_thread['title'] == "New Chat":
        current_thread['title'] = user_input[:40]  # truncate


    CONFIG = {'configurable' : {'thread_id' : st.session_state['thread_id']}}

    
    with st.chat_message('assistant'):
        def ai_only_stream():
            for message_chunk , metadata in chatbot.stream(
                {'messages' : [HumanMessage(content=user_input)]},
                config = CONFIG,
                stream_mode='messages'
            ):
                if isinstance(message_chunk , AIMessage):
                    # yield only assistant tokens
                    yield message_chunk.content


        ai_message = st.write_stream(ai_only_stream())

    

    st.session_state['message_history'].append({'role' : 'assistant' , 'content' : ai_message})
