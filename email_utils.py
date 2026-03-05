import smtplib
from email.mime.text import MIMEText
import os

def send_email(url: str, status_code: int, recipient: str):
    msg = MIMEText(f"Alert: {url} is now returning status {status_code}")
    msg['Subject'] = f'MonitorUp Alert - {url}'
    msg['From'] = os.getenv('EMAIL_FROM')
    msg['To'] = recipient

    with smtplib.SMTP(os.getenv('EMAIL_HOST'), int(os.getenv('EMAIL_PORT', 587))) as server:
        server.starttls()
        server.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASSWORD'))
        server.send_message(msg)
