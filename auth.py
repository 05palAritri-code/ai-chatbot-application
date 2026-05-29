from db_manager import get_connection
from typing import Any, Dict, Optional, TypedDict, Annotated
import hashlib
from db_manager import get_connection

conn = get_connection()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(email, username, password):

    try:

        cursor = conn.cursor()

        # check email
        cursor.execute(
            "SELECT id FROM users WHERE email=%s",
            (email,)
        )

        if cursor.fetchone():

            return "email_exists"

        # check username
        cursor.execute(
            "SELECT id FROM users WHERE username=%s",
            (username,)
        )

        if cursor.fetchone():

            return "username_exists"

        # create user
        cursor.execute(
            """
            INSERT INTO users
            (email, username, password)
            VALUES (%s, %s, %s)
            """,
            (
                email,
                username,
                hash_password(password)
            )
        )

        conn.commit()
        print("✅ User inserted successfully")
        return "success"

    except Exception as e:

        print("CREATE USER ERROR:", e)

        return "error"

def login_user(email, password):
    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT username FROM users WHERE email=%s AND password=%s",
            (email, hash_password(password))
        )

        return cursor.fetchone()

    except Exception as e:
        print("LOGIN ERROR:", e)
        return None