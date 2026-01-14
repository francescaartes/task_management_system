import smtplib
import ssl
import random
from email.message import EmailMessage
from dotenv import load_dotenv
import os

load_dotenv()

SENDER_EMAIL = os.getenv("EMAIL")
SENDER_PASSWORD = os.getenv("PASSWORD")

def generate_otp():
    return str(random.randint(100000, 999999))

def send_reset_code(receiver_email):
    otp = generate_otp()
    
    subject = "TaskFlow Password Reset"
    body = f"""
    Your verification code is: {otp}
    
    If you did not request this, please ignore this email.
    """

    em = EmailMessage()
    em['From'] = SENDER_EMAIL
    em['To'] = receiver_email
    em['Subject'] = subject
    em.set_content(body)

    context = ssl.create_default_context()

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.ehlo()
            smtp.starttls(context=context)
            smtp.ehlo() 
            
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.sendmail(SENDER_EMAIL, receiver_email, em.as_string())
            
        return otp
    except Exception as e:
        print(f"Email Error: {e}")
        return None