import smtplib
from email.mime.text import MIMEText
import os
from celery_app import celery_app


def _send(recipient: str, subject: str, html: str, sender: str ):
    
    msg = MIMEText(html, "html")
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient

    with smtplib.SMTP(os.getenv('EMAIL_HOST'), int(os.getenv('EMAIL_PORT', 587))) as server:
        server.starttls()
        server.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASSWORD'))
        server.send_message(msg)


def _layout(inner: str) -> str:
    
    return f"""\
<div style="margin:0;padding:0;background-color:#f4f4f7;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
  <div style="max-width:480px;margin:0 auto;padding:32px 16px;">
    <div style="background:#1a1a2e;border-radius:12px 12px 0 0;padding:24px;text-align:center;">
      <span style="color:#ffffff;font-size:22px;font-weight:700;letter-spacing:0.5px;">Monitor<span style="color:#4ade80;">Up</span></span>
    </div>
    <div style="background:#ffffff;border-radius:0 0 12px 12px;padding:32px 28px;box-shadow:0 1px 3px rgba(0,0,0,0.08);">
{inner}
    </div>
    <p style="text-align:center;font-size:12px;color:#9ca3af;margin-top:16px;">MonitorUp &middot; uptime monitoring</p>
  </div>
</div>"""


def send_email(url: str, status_code: int, recipient: str):
    inner = f"""\
      <h1 style="margin:0 0 8px;font-size:18px;color:#1a1a2e;">Status alert</h1>
      <p style="margin:0 0 20px;font-size:15px;line-height:1.6;color:#4b5563;">One of your monitors just changed status.</p>
      <div style="background:#f9fafb;border-left:4px solid #f59e0b;border-radius:6px;padding:16px;margin-bottom:20px;">
        <p style="margin:0;font-size:14px;line-height:1.6;color:#374151;word-break:break-all;">
          <strong style="color:#1a1a2e;">{url}</strong><br>
          is now returning status <strong>{status_code}</strong>
        </p>
      </div>
      <p style="margin:0;font-size:13px;color:#9ca3af;">You're receiving this because you monitor this URL on MonitorUp.</p>"""
    _send(recipient, f'MonitorUp Alert - {url}', _layout(inner), os.getenv('EMAIL_ALERTS'))

@celery_app.task
def send_verification_email(recipient: str, token: str):
    
    if token == "user already exists":
        inner = """\
      <h1 style="margin:0 0 8px;font-size:18px;color:#1a1a2e;">You already have an account</h1>
      <p style="margin:0 0 24px;font-size:15px;line-height:1.6;color:#4b5563;">Someone just tried to sign up with this email, but you already have a MonitorUp account. If that was you, simply log in.</p>
      <div style="text-align:center;margin-bottom:24px;">
        <a href="https://monitorup.me/login" style="display:inline-block;background:#4ade80;color:#1a1a2e;font-size:15px;font-weight:600;text-decoration:none;padding:13px 32px;border-radius:8px;">Log in</a>
      </div>
      <p style="margin:0;font-size:13px;color:#9ca3af;">If you didn't try to sign up, you can safely ignore this email.</p>"""
        _send(recipient, 'MonitorUp - You already have an account', _layout(inner), os.getenv('EMAIL_VERIFY'))
        return

    link = f"https://monitorup.me/verify?token={token}"
    inner = f"""\
      <h1 style="margin:0 0 8px;font-size:18px;color:#1a1a2e;">Confirm your email</h1>
      <p style="margin:0 0 24px;font-size:15px;line-height:1.6;color:#4b5563;">Welcome to MonitorUp! Tap the button below to verify your email and activate your account.</p>
      <div style="text-align:center;margin-bottom:24px;">
        <a href="{link}" style="display:inline-block;background:#4ade80;color:#1a1a2e;font-size:15px;font-weight:600;text-decoration:none;padding:13px 32px;border-radius:8px;">Verify email</a>
      </div>
      <p style="margin:0 0 8px;font-size:13px;color:#6b7280;">Or paste this link into your browser:</p>
      <p style="margin:0 0 24px;font-size:13px;word-break:break-all;"><a href="{link}" style="color:#2563eb;">{link}</a></p>
      <p style="margin:0;font-size:13px;color:#9ca3af;">If you didn't create an account, you can safely ignore this email.</p>"""
    _send(recipient, 'MonitorUp Email Verification', _layout(inner), os.getenv('EMAIL_VERIFY'))
