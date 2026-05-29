from utils import (generate_thread_id)
import streamlit as st
from db_manager import get_connection
from ingest import _THREAD_RETRIEVERS, _THREAD_METADATA

def reset_chat():
    thread_id = generate_thread_id()
    # save_thread(thread_id,st.session_state.username)
    st.session_state['thread_id'] = thread_id
    add_threads(st.session_state['thread_id'])

    st.session_state['message_history'] = []

def add_thread(thread_id):
    if thread_id not in st.session_state["chat_threads"]:
        st.session_state["chat_threads"].append(thread_id)

def add_threads(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def retrive_threads(username):

    conn = None
    cursor = None

    try:

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT thread_id
            FROM threads
            WHERE username=%s
            ORDER BY created_at DESC
            """,
            (username,)
        )

        rows = cursor.fetchall()

        return [row["thread_id"] for row in rows]

    except Exception as e:

        print("RETRIEVE THREAD ERROR:", e)
        return []

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()

    
def thread_has_document(thread_id : str) -> bool:
    return str(thread_id) in _THREAD_RETRIEVERS

def thread_document_metadata(thread_id : str) -> dict:
    return _THREAD_METADATA.get(str(thread_id),{})

def delete_thread(thread_id):

    try:

        conn = get_connection()
        cursor = conn.cursor()

        # delete messages first
        cursor.execute(
            """
            DELETE FROM messages
            WHERE thread_id=%s
            """,
            (thread_id,)
        )

        # delete thread
        cursor.execute(
            """
            DELETE FROM threads
            WHERE thread_id=%s
            """,
            (thread_id,)
        )

        conn.commit()

    except Exception as e:

        print("DELETE THREAD ERROR:", e)


def rename_thread(thread_id, new_title):

    try:

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE threads
            SET title=%s
            WHERE thread_id=%s
            """,
            (new_title, thread_id)
        )

        conn.commit()

    except Exception as e:

        print("RENAME THREAD ERROR:", e)

def get_thread_title(thread_id):

    try:

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT title
            FROM threads
            WHERE thread_id=%s
            """,
            (thread_id,)
        )

        row = cursor.fetchone()

        if row:
            return row["title"]

    except Exception as e:

        print("GET TITLE ERROR:", e)

    return None


