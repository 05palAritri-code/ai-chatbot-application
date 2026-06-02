import smtplib
import os
from dotenv import load_dotenv
load_dotenv()
EMAIL = os.getenv("EMAIL_ADDRESS")
APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
print("EMAIL =", EMAIL)
print("PASSWORD =", APP_PASSWORD)
server = smtplib.SMTP("smtp.gmail.com", 587)
server.starttls()

server.login(
    EMAIL,
    APP_PASSWORD
)

print("LOGIN SUCCESS")