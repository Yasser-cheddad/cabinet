import smtplib
from email.mime.text import MIMEText
import os
from django.conf import settings

def send_email(to, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = 'cheddadyasse2002@gmail.com'
    msg['To'] = to
    
    # Get email credentials from settings
    email = 'cheddadyasse2002@gmail.com'
    password = 'qnhp vejy qjmk ipwa'  # App password for Gmail
    smtp_host = 'smtp.gmail.com'
    smtp_port = 587
    
    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(email, password)
            server.send_message(msg)
            return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False