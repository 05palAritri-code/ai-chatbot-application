from db_manager import get_connection
import streamlit as st
from chat import workflow


def save_thread(thread_id, username, title):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO threads 
            (thread_id, username, title)
            VALUES (%s, %s, %s)
            ON CONFLICT (thread_id) DO NOTHING
            """,
            (thread_id, username, title)
        )

        conn.commit()

    except Exception as e:
        print("SAVE THREAD ERROR:", e)


def update_thread_title(thread_id , title):

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE threads
            SET title=%s
            WHERE thread_id=%s
            """,
            (title , thread_id)
        )

        conn.commit()

    except Exception as e:

        print("UPDATE TITLE ERROR:", e)

def save_message(thread_id, role, content):

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO messages
            (thread_id, role, content)
            VALUES (%s, %s, %s)
            """,
            (thread_id, role, content)
        )

        conn.commit()

    except Exception as e:

        print("SAVE MESSAGE ERROR:", e)

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

# def load_conversation(thread_id):
#     state = workflow.get_state(
#         config={
#             'configurable': {
#                 'thread_id': thread_id,
#                 'user': st.session_state.username
#             }
#         }
#     )
#     return state

def load_messages(thread_id):

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT role, content
            FROM messages
            WHERE thread_id=%s
            ORDER BY id
            """,
            (thread_id,)
        )

        rows = cursor.fetchall()

        return [
            {
                "role": row["role"],
                "content": row["content"]
            }
            for row in rows
        ]

    except Exception as e:

        print("LOAD MESSAGE ERROR:", e)

        return []