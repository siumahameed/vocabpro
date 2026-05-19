"""
VocabPro Email Sender Module
Sends daily vocabulary via Brevo SMTP (free tier: 300 emails/day)
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_HOST = os.environ.get("BREVO_SMTP_HOST", "smtp-relay.sendinblue.com")
SMTP_PORT = int(os.environ.get("BREVO_SMTP_PORT", "587"))
SMTP_LOGIN = os.environ.get("BREVO_SMTP_LOGIN", "")
SMTP_PASSWORD = os.environ.get("BREVO_SMTP_PASSWORD", "")
SENDER_EMAIL = os.environ.get("BREVO_SENDER_EMAIL", SMTP_LOGIN)
SENDER_NAME = os.environ.get("BREVO_SENDER_NAME", "VocabPro")


def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """Send an HTML email via Brevo SMTP"""
    if not SMTP_LOGIN or not SMTP_PASSWORD:
        print("Email error: SMTP credentials not configured")
        return False
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
        msg['To'] = to_email
        msg.attach(MIMEText(html_content, 'html'))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_LOGIN, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Email error to {to_email}: {e}")
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
            <a href="https://vocabpro.onrender.com/dashboard" style="display:inline-block; background:#3b82f6; color:#fff; padding:10px 24px; border-radius:8px; text-decoration:none; font-weight:600; font-size:14px;">Open Dashboard</a>
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
            <a href="https://vocabpro.onrender.com/dashboard" style="display:inline-block; background:#3b82f6; color:#fff; padding:10px 24px; border-radius:8px; text-decoration:none; font-weight:600; font-size:14px;">Go to Dashboard</a>
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
                print(f"Email sent to {email}")
            else:
                failed += 1
                print(f"Email failed to {email}")
        except Exception as e:
            print(f"Error sending email to {email}: {e}")
            failed += 1

    print(f"Email broadcast complete: {sent} sent, {failed} failed")
    return {"sent": sent, "failed": failed, "total": total}
