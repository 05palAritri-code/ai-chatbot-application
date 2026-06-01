import hashlib
from streamlit import st
import uuid

def generate_thread_id():
    thread_id = str(uuid.uuid4())
    
    return thread_id

def add_threads(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def reset_chat():
    thread_id = generate_thread_id()
    # save_thread(thread_id,st.session_state.username)
    st.session_state['thread_id'] = thread_id
    add_threads(st.session_state['thread_id'])

    st.session_state['message_history'] = []

def get_file_hash(file_bytes):

    return hashlib.md5(file_bytes).hexdigest()