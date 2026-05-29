import hashlib
import re
from turtle import st
import uuid
from db_manager import get_connection

conn = get_connection()

def clean_response(text: str) -> str:

    patterns = [
        r"</function>",
        r"function=.*?>",
        r"groq\.APIError.*",
        r"failed_generation.*"
    ]

    for pattern in patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    return text.strip()

def generate_thread_id():
    thread_id = str(uuid.uuid4())
    
    return thread_id

def load_conversation(thread_id):
    state = workflow.get_state(
        config={
            'configurable': {
                'thread_id': thread_id,
                'user': st.session_state.username
            }
        }
    )
    return state

def load_messages(thread_id):

    try:

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
    



def get_file_hash(file_bytes):

    return hashlib.md5(file_bytes).hexdigest()

def save_thread(thread_id, username, title):
    try:
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
def update_thread_title(thread_id, title):

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE threads
            SET title=%s
            WHERE thread_id=%s
            """,
            (title, thread_id)
        )

        conn.commit()

    except Exception as e:

        print("UPDATE TITLE ERROR:", e)
def save_message(thread_id, role, content):

    try:

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