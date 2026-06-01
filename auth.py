from db_manager import get_connection
import bcrypt
import random
from datetime import datetime, timedelta
import smtplib
import os
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")




def hash_password(password):

    hashed = bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    )

    return hashed.decode()

def send_otp_email(receiver_email, otp):

    message = MIMEText(
        f"""
        Your verification code is:

        {otp}

        This code expires in 10 minutes.
        """
            )

    message["Subject"] = "Verify Your Account"
    message["From"] = EMAIL_ADDRESS
    message["To"] = receiver_email

    try:

        server = smtplib.SMTP("smtp.gmail.com", 587)

        server.starttls()

        server.login(
            EMAIL_ADDRESS,
            EMAIL_PASSWORD
        )

        server.send_message(message)

        server.quit()

        return True

    except Exception as e:

        print("EMAIL ERROR:", e)

        return False
    
def verify_otp(email, entered_otp):

    conn = None
    cursor = None

    try:

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT otp_code, otp_expiry
            FROM users
            WHERE email=%s
            """,
            (email,)
        )

        user = cursor.fetchone()

        if not user:
            return False

        stored_otp = user["otp_code"]
        otp_expiry = user["otp_expiry"]

        # OTP expired
        if datetime.now() > otp_expiry:
            return False

        # OTP mismatch
        if entered_otp != stored_otp:
            return False

        # Mark account verified
        cursor.execute(
            """
            UPDATE users
            SET
                is_verified = TRUE,
                otp_code = NULL,
                otp_expiry = NULL
            WHERE email=%s
            """,
            (email,)
        )

        conn.commit()

        return True

    except Exception as e:

        print("VERIFY OTP ERROR:", e)
        return False

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()
def create_user(email, username, password):

    try:

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM users WHERE email=%s",
            (email,)
        )

        if cursor.fetchone():
            return "email_exists"

        cursor.execute(
            "SELECT id FROM users WHERE username=%s",
            (username,)
        )

        if cursor.fetchone():
            return "username_exists"

        otp = generate_otp()

        expiry = datetime.now() + timedelta(minutes=10)

        cursor.execute(
            """
            INSERT INTO users
            (
                email,
                username,
                password,
                otp_code,
                otp_expiry,
                is_verified
            )
            VALUES (%s,%s,%s,%s,%s,%s)
            """,
            (
                email,
                username,
                hash_password(password),
                otp,
                expiry,
                False
            )
        )

        conn.commit()

        send_otp_email(email, otp)

        return "otp_sent"

    except Exception as e:

        print("CREATE USER ERROR:", e)

        return "error"

def login_user(email, password):

    try:

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT username,is_verified
            FROM users
            WHERE email=%s
            AND password=%s
            """,
            (
                email,
                hash_password(password)
            )
        )

        user = cursor.fetchone()

        if not user:
            return None

        if not user["is_verified"]:
            return "not_verified"

        return user

    except Exception as e:

        print("LOGIN ERROR:", e)

        return None
    
def generate_otp():

    return str(random.randint(100000, 999999))