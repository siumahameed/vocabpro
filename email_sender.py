"""
VocabPro Email Sender Module
Sends daily vocabulary via Gmail SMTP (primary) or Brevo API (fallback)
"""

import os
import json
import smtplib
import urllib.request
import urllib.error
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Gmail SMTP Configuration (strip quotes that Render might add)
GMAIL_USER = os.environ.get("GMAIL_USER", "").strip('"').strip("'")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "").strip('"').strip("'")

# Brevo API Configuration (fallback)
BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
SENDER_EMAIL = os.environ.get("BREVO_SENDER_EMAIL", "")
SENDER_NAME = os.environ.get("BREVO_SENDER_NAME", "VocabPro")


def _send_via_gmail(to_email: str, subject: str, html_content: str) -> bool:
    """Send email via Gmail SMTP"""
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        print(f"Gmail SMTP not configured: user={bool(GMAIL_USER)}, pass={bool(GMAIL_APP_PASSWORD)}")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"VocabPro <{GMAIL_USER}>"
    msg["To"] = to_email
    msg.attach(MIMEText(html_content, "html"))

    try:
        print(f"Connecting to Gmail SMTP for {to_email}...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, to_email, msg.as_string())
        print(f"Email sent to {to_email} (Gmail SMTP)")
        return True
    except Exception as e:
        print(f"Gmail SMTP error to {to_email}: {type(e).__name__}: {e}")
        return False


def _send_via_brevo(to_email: str, subject: str, html_content: str) -> bool:
    """Send email via Brevo API (fallback)"""
    if not BREVO_API_KEY or not SENDER_EMAIL:
        return False

    payload = json.dumps({
        "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_content
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.brevo.com/v3/smtp/email",
        data=payload,
        headers={
            "accept": "application/json",
            "content-type": "application/json",
            "api-key": BREVO_API_KEY
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status in (200, 201):
                print(f"Email sent to {to_email} (Brevo)")
                return True
            print(f"Brevo error to {to_email}: HTTP {resp.status}")
            return False
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        print(f"Brevo error to {to_email}: HTTP {e.code} - {body}")
        return False
    except Exception as e:
        print(f"Brevo error to {to_email}: {e}")
        return False


def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """Send an HTML email — tries Brevo first (HTTPS, works on Render), falls back to Gmail SMTP"""
    # Try Brevo first (HTTPS API — works on Render free tier)
    if BREVO_API_KEY and SENDER_EMAIL:
        result = _send_via_brevo(to_email, subject, html_content)
        if result:
            return True
        print(f"Brevo failed for {to_email}, trying Gmail SMTP...")

    # Fallback to Gmail SMTP (blocked on Render, works locally)
    if GMAIL_USER and GMAIL_APP_PASSWORD:
        return _send_via_gmail(to_email, subject, html_content)

    print("Email error: No email provider configured")
    return False


def create_vocab_email_html(name: str, words: list) -> str:
    """Build a clean HTML email with vocabulary words"""
    word_cards = ""
    for i, w in enumerate(words, 1):
        word = w.get('word', '')
        phonetic = w.get('phonetic', '')
        meaning = w.get('meaning_bn', w.get('meaning', ''))
        example = w.get('example', '')
        word_cards += f"""
        <div style="background: #f8fafc; border-left: 4px solid #3b82f6; border-radius: 8px; padding: 14px 18px; margin-bottom: 10px;">
            <div style="display: flex; align-items: baseline; gap: 8px;">
                <span style="color: #94a3b8; font-size: 13px; font-weight: 600;">{i}.</span>
                <span style="font-size: 19px; font-weight: 700; color: #1e40af;">{word}</span>
                <span style="color: #94a3b8; font-size: 13px;">{phonetic}</span>
            </div>
            <div style="color: #374151; font-size: 15px; margin-top: 4px; font-weight: 600; padding-left: 22px;">{meaning}</div>
            <div style="color: #6b7280; font-size: 13px; margin-top: 4px; font-style: italic; padding-left: 22px;">"{example}"</div>
        </div>
        """

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0; padding:0; background:#f0f4f8;">
<div style="max-width:580px; margin:20px auto; font-family:'Segoe UI',Arial,sans-serif;">
    <div style="background:linear-gradient(135deg,#1e40af,#3b82f6); border-radius:16px 16px 0 0; padding:28px 32px; text-align:center;">
        <h1 style="color:#fff; margin:0; font-size:24px;">VocabPro</h1>
        <p style="color:#bfdbfe; margin:6px 0 0; font-size:14px;">Daily Vocabulary for {name}</p>
    </div>
    <div style="background:#fff; border-radius:0 0 16px 16px; padding:28px 32px; box-shadow:0 4px 12px rgba(0,0,0,0.08);">
        <p style="color:#374151; font-size:15px; margin:0 0 20px;">Hi <strong>{name}</strong>, here are your <strong>10 new words</strong> for today!</p>
        {word_cards}
        <div style="text-align:center; margin-top:24px; padding-top:16px; border-top:1px solid #e5e7eb;">
            <a href="https://vocabpro-dgow.onrender.com/login" style="display:inline-block; background:#3b82f6; color:#fff; padding:10px 24px; border-radius:8px; text-decoration:none; font-weight:600; font-size:14px;">Open Dashboard</a>
        </div>
    </div>
    <p style="text-align:center; color:#9ca3af; font-size:11px; margin-top:12px;">VocabPro &mdash; Learn 10 words every day</p>
</div>
</body>
</html>"""


def create_welcome_email_html(name: str) -> str:
    """Build welcome email HTML"""
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0; padding:0; background:#f0f4f8;">
<div style="max-width:580px; margin:20px auto; font-family:'Segoe UI',Arial,sans-serif;">
    <div style="background:linear-gradient(135deg,#1e40af,#3b82f6); border-radius:16px 16px 0 0; padding:28px 32px; text-align:center;">
        <h1 style="color:#fff; margin:0; font-size:24px;">Welcome to VocabPro!</h1>
    </div>
    <div style="background:#fff; border-radius:0 0 16px 16px; padding:28px 32px; box-shadow:0 4px 12px rgba(0,0,0,0.08);">
        <p style="color:#374151; font-size:15px;">Hi <strong>{name}</strong>,</p>
        <p style="color:#374151; font-size:15px;">Your account has been created successfully. You'll receive <strong>10 vocabulary words daily</strong> at your preferred time.</p>
        <p style="color:#374151; font-size:15px;">Here's what you can do:</p>
        <ul style="color:#374151; font-size:14px; line-height:1.8;">
            <li>Take daily quizzes to test your knowledge</li>
            <li>Join daily and weekly contests</li>
            <li>Track your progress on the leaderboard</li>
            <li>Chat with C_ium, your AI English companion</li>
        </ul>
        <div style="text-align:center; margin-top:24px;">
            <a href="https://vocabpro-dgow.onrender.com/login" style="display:inline-block; background:#3b82f6; color:#fff; padding:10px 24px; border-radius:8px; text-decoration:none; font-weight:600; font-size:14px;">Go to Dashboard</a>
        </div>
    </div>
    <p style="text-align:center; color:#9ca3af; font-size:11px; margin-top:12px;">VocabPro &mdash; Learn 10 words every day</p>
</div>
</body>
</html>"""


def create_password_reset_email_html(name: str, code: str) -> str:
    """Build password reset email HTML"""
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0; padding:0; background:#f0f4f8;">
<div style="max-width:580px; margin:20px auto; font-family:'Segoe UI',Arial,sans-serif;">
    <div style="background:linear-gradient(135deg,#dc2626,#ef4444); border-radius:16px 16px 0 0; padding:28px 32px; text-align:center;">
        <h1 style="color:#fff; margin:0; font-size:22px;">Password Reset</h1>
    </div>
    <div style="background:#fff; border-radius:0 0 16px 16px; padding:28px 32px; box-shadow:0 4px 12px rgba(0,0,0,0.08);">
        <p style="color:#374151; font-size:15px;">Hi <strong>{name}</strong>,</p>
        <p style="color:#374151; font-size:15px;">Your password reset code is:</p>
        <div style="text-align:center; margin:20px 0;">
            <span style="font-size:32px; font-weight:700; color:#1e40af; letter-spacing:6px; background:#f0f7ff; padding:12px 24px; border-radius:8px;">{code}</span>
        </div>
        <p style="color:#6b7280; font-size:13px;">This code expires in 15 minutes. If you didn't request this, ignore this email.</p>
    </div>
</div>
</body>
</html>"""


def send_daily_vocab_email(user: dict, words: list) -> bool:
    """Send daily vocabulary email to a user"""
    name = user.get('name', 'Learner')
    email = user.get('email', '')
    if not email:
        return False
    subject = "Your Daily Vocabulary from VocabPro"
    html = create_vocab_email_html(name, words)
    return send_email(email, subject, html)


def send_welcome_email(user: dict) -> bool:
    """Send welcome email to a new user"""
    name = user.get('name', 'Learner')
    email = user.get('email', '')
    if not email:
        return False
    subject = "Welcome to VocabPro!"
    html = create_welcome_email_html(name)
    return send_email(email, subject, html)


def send_password_reset_email(user: dict, code: str) -> bool:
    """Send password reset code via email"""
    name = user.get('name', 'Learner')
    email = user.get('email', '')
    if not email:
        return False
    subject = "VocabPro - Password Reset Code"
    html = create_password_reset_email_html(name, code)
    return send_email(email, subject, html)


def send_to_email_subscribers(subscribers: list) -> dict:
    """Send daily vocabulary to all email subscribers"""
    import whatsapp_bot  # reuse get_daily_words, get_vocabulary_count

    sent = 0
    failed = 0
    total = len(subscribers)

    print(f"Starting email broadcast to {total} subscribers...")

    for subscriber in subscribers:
        email = subscriber.get('email', '')
        user_id = subscriber.get('id')
        last_index = subscriber.get('last_word_index', 0)
        user_category = subscriber.get('preferred_category', 'ielts')

        if not email:
            continue

        try:
            words = whatsapp_bot.get_daily_words(10, last_index, category=user_category)

            if send_daily_vocab_email(subscriber, words):
                sent += 1
                total_words = whatsapp_bot.get_vocabulary_count()
                new_index = (last_index + 10) % total_words if total_words > 0 else last_index + 10
                import database
                database.update_last_word_index(user_id, new_index)
                database.increment_leaderboard_words(user_id, 10)
                database.update_user_progress(user_id)
                database.update_last_word_sent_date(user_id)
                print(f"Email sent to {email}")
            else:
                failed += 1
                print(f"Email failed to {email}")
        except Exception as e:
            print(f"Error sending email to {email}: {e}")
            failed += 1

    print(f"Email broadcast complete: {sent} sent, {failed} failed")
    return {"sent": sent, "failed": failed, "total": total}


def send_broadcast_email(user: dict, message: str) -> bool:
    """Send a broadcast message to a single user via email"""
    name = user.get('name', 'Learner')
    email = user.get('email', '')
    if not email:
        return False
    subject = "VocabPro - Important Update"
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#f0f4f8;">
<div style="max-width:580px;margin:20px auto;font-family:'Segoe UI',Arial,sans-serif;">
    <div style="background:linear-gradient(135deg,#1e40af,#3b82f6);border-radius:16px 16px 0 0;padding:28px 32px;text-align:center;">
        <h1 style="color:#fff;margin:0;font-size:24px;">VocabPro</h1>
    </div>
    <div style="background:#fff;padding:28px 32px;border-radius:0 0 16px 16px;">
        <p style="color:#374151;font-size:15px;">Hi {name},</p>
        <p style="color:#374151;font-size:15px;line-height:1.6;">{message}</p>
        <p style="color:#6b7280;font-size:13px;margin-top:24px;">— The VocabPro Team</p>
    </div>
</div>
</body></html>"""
    return send_email(email, subject, html)
