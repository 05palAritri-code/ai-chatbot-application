import psycopg2
from psycopg2.extras import RealDictCursor
import os

DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():

    return psycopg2.connect(
        DATABASE_URL,
        cursor_factory=RealDictCursor
    )


def initialize_database():

    conn = get_connection()
    cursor = conn.cursor()


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email TEXT UNIQUE,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS threads (
        id SERIAL PRIMARY KEY,
        thread_id TEXT UNIQUE,
        username TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id SERIAL PRIMARY KEY,
        thread_id TEXT,
        role TEXT,
        content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()

    checkpointer = None

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
def update_thread_title(thread_id, title):

    try:
        conn = get_connection()
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