import hashlib
import streamlit as st
import uuid
from back_utils import ( get_thread_title , load_messages )

def generate_thread_id():
    thread_id = str(uuid.uuid4())
    
    return thread_id

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def reset_chat():
    thread_id = generate_thread_id()
    # save_thread(thread_id,st.session_state.username)
    st.session_state['thread_id'] = thread_id
    add_thread(st.session_state['thread_id'])

    st.session_state['message_history'] = []

def generate_title(thread_id):


    messages = load_messages(thread_id)

    if len(messages) > 0:

        msg = messages[0]["content"]
        snap = " ".join(msg.split()[:5])
        get_thread_title(snap)
    return snap

    

def get_file_hash(file_bytes):

    return hashlib.md5(file_bytes).hexdigest()