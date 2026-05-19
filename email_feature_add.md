# VocabPro - Email Feature Addition Plan

## Executive Summary

This document outlines the complete plan to add **email-based vocabulary delivery** as a free alternative to WhatsApp for VocabPro users. This solves the Green API Developer plan's 3-chat limit problem and provides a zero-cost delivery channel.

---

## Problem Statement

### Current Situation
- **Green API Developer Plan (Free):** Only 3 WhatsApp chats allowed
- **VocabPro Usage:** Each user needs individual WhatsApp delivery
- **Scaling Issue:** 10+ users will exceed the 3-chat limit
- **Cost:** Green API Business plan = $12/month (not affordable for free MVP)

### The Problem
```
Developer Plan Limit: 3 chats
VocabPro Model: 1 chat per user

At 10 users → FAILURE ❌ (Green API will reject messages beyond 3 chats)
```

### Constraints
1. **Zero additional cost** — No paid subscriptions, no per-message fees
2. **Users must receive daily words** — Core value proposition must continue
3. **Email field already exists** in the database (`email TEXT UNIQUE NOT NULL`)

---

## Solution Overview

### Two-Channel Architecture (NEW)

```
┌─────────────────────────────────────────────────────────┐
│              VocabPro Scheduler                         │
│         (every 15 minutes, same as now)                  │
└───────────────┬─────────────────────────────────────────┘
                │
        ┌───────▼────────┐
        │  Decision:     │
        │  user.delivery │
        │  _channel     │
        └───────┬────────┘
                │
    ┌──────────┴──────────┐
    │                      │
    ▼                      ▼
┌─────────┐         ┌──────────┐
│ WhatsApp│         │  Email   │
│ (Green) │         │ (Brevo)  │
└─────────┘         └──────────┘
```

### Hybrid Delivery Model
- Users choose their **preferred channel** (WhatsApp OR Email)
- Default: **Email** for new users (free for you)
- Existing WhatsApp users can keep WhatsApp OR switch to email
- Both channels use the **same scheduler** (every 15 min)
- Same content: 10 vocabulary words with Bengali meanings

---

## What Already Exists

| Component | Status | Location |
|-----------|--------|----------|
| Email field in DB | ✅ Ready | `database.py:84` |
| User signup form | ✅ Ready | `templates/signup.html` |
| User email storage | ✅ Ready | `users.email` column |
| Scheduler | ✅ Ready | `main.py:71-77, 1554-1569` |
| Vocab message builder | ✅ Ready | `whatsapp_bot.py:505-529` |
| Dashboard UI | ✅ Ready | `templates/dashboard.html` |
| PostgreSQL (production) | ✅ Ready | `.env` |

---

## What Needs to Be Built

### Phase 1: Core Email System (No Cost)

#### Step 1.1: Add Email Credentials to `.env`
**File:** `.env`
```env
# Brevo SMTP (Free - 300 emails/day)
BREVO_SMTP_HOST=smtp-relay.sendinblue.com
BREVO_SMTP_PORT=587
BREVO_SMTP_LOGIN=your@email.com
BREVO_SMTP_PASSWORD=your-app-password
BREVO_SENDER_EMAIL=your@email.com
BREVO_SENDER_NAME=VocabPro
```

**Action for you:**
1. Go to [brevo.com](https://brevo.com) → Sign up free (no credit card)
2. Verify your email domain
3. Go to SMTP & API → SMTP Settings
4. Copy host, port, login, and generate an SMTP key

#### Step 1.2: Create Email Module
**New File:** `email_sender.py`

```python
# email_sender.py
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .env import load_dotenv

load_dotenv()

SMTP_HOST = os.environ.get("BREVO_SMTP_HOST", "smtp-relay.sendinblue.com")
SMTP_PORT = int(os.environ.get("BREVO_SMTP_PORT", "587"))
SMTP_LOGIN = os.environ.get("BREVO_SMTP_LOGIN")
SMTP_PASSWORD = os.environ.get("BREVO_SMTP_PASSWORD")
SENDER_EMAIL = os.environ.get("BREVO_SENDER_EMAIL", SMTP_LOGIN)
SENDER_NAME = os.environ.get("BREVO_SENDER_NAME", "VocabPro")

def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """Send email via SMTP"""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
        msg['To'] = to_email

        part1 = MIMEText(html_content, 'html')
        msg.attach(part1)

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_LOGIN, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())

        return True
    except Exception as e:
        print(f"Email error to {to_email}: {e}")
        return False

def create_vocab_email_content(name: str, words: list) -> str:
    """Create beautiful HTML email with vocabulary words"""
    words_html = ""
    for w in words:
        words_html += f"""
        <div style="border-left: 4px solid #3b82f6; padding: 12px 16px; margin-bottom: 12px; background: #f8fafc; border-radius: 8px;">
            <div style="font-size: 20px; font-weight: bold; color: #1e40af;">{w['word']}</div>
            <div style="color: #64748b; font-size: 13px; margin-top: 4px;">{w.get('phonetic', '')}</div>
            <div style="color: #374151; font-size: 16px; margin-top: 6px; font-weight: 600;">{w.get('meaning_bn', w.get('meaning', ''))}</div>
            <div style="color: #6b7280; font-size: 14px; margin-top: 6px; font-style: italic;">"{w.get('example', '')}"</div>
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background: #f0fdf4;">
        <div style="background: white; border-radius: 16px; padding: 32px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <div style="text-align: center; margin-bottom: 24px;">
                <h1 style="color: #1e40af; margin: 0;">📚 VocabPro</h1>
                <p style="color: #6b7280; margin: 8px 0 0;">Daily Vocabulary for {name}</p>
            </div>
            <div style="margin-bottom: 24px;">
                <p style="font-size: 15px; color: #374151;">Hi {name}, here are your <strong>10 new words</strong> for today!</p>
            </div>
            {words_html}
            <div style="text-align: center; margin-top: 24px; padding-top: 16px; border-top: 1px solid #e5e7eb;">
                <p style="color: #9ca3af; font-size: 12px;">VocabPro — Learn 10 words every day<br>Vocabulary delivered at your preferred time</p>
            </div>
        </div>
    </body>
    </html>
    """

def send_daily_vocab_email(user: dict, words: list) -> bool:
    """Send daily vocabulary email to a user"""
    subject = "📚 Your Daily Vocabulary from VocabPro"
    html = create_vocab_email_content(user.get('name', 'Learner'), words)
    return send_email(user.get('email'), subject, html)
```

#### Step 1.3: Add `delivery_channel` to Database
**File:** `database.py`

Add a new column `delivery_channel` to the users table:
```python
# Migration: add delivery_channel if missing
try:
    if USE_POSTGRES:
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS delivery_channel TEXT DEFAULT 'email'")
    else:
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'delivery_channel' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN delivery_channel TEXT DEFAULT 'email'")
    conn.commit()
except Exception as e:
    print(f"Migration note: {e}")
```

**Values:**
- `email` = Send via Brevo SMTP (default, free)
- `whatsapp` = Send via Green API (limited to 3 chats on Developer plan)
- `both` = Send via both channels (use this selectively)

#### Step 1.4: Modify Scheduler to Support Both Channels
**File:** `main.py` — Update `send_daily_vocabulary()` function

```python
def send_daily_vocabulary():
    """Send daily vocabulary to all active subscribers"""
    current_time = datetime.now().strftime("%H:%M")
    print(f"[{datetime.now()}] Checking for users with preferred time: {current_time}")

    users = database.get_users_by_time(current_time)

    if users:
        print(f"Found {len(users)} users wanting words at {current_time}")

        # Separate by delivery channel
        email_users = [u for u in users if u.get('delivery_channel') in ('email', 'both')]
        whatsapp_users = [u for u in users if u.get('delivery_channel') in ('whatsapp', 'both')]

        # Email channel
        if email_users:
            result = email_sender.send_to_email_subscribers(email_users)
            print(f"Email vocab sent: {result}")

        # WhatsApp channel (with chat limit protection)
        if whatsapp_users:
            result = whatsapp_bot.send_to_all_subscribers(whatsapp_users)
            print(f"WhatsApp vocab sent: {result}")
    else:
        print(f"No users scheduled for {current_time}")
```

#### Step 1.5: Create Email Sending Function
**File:** `email_sender.py`

```python
def send_to_email_subscribers(subscribers: list):
    """Send daily vocabulary email to all email subscribers"""
    import database
    import whatsapp_bot  # reuse word-fetching logic

    sent = 0
    failed = 0

    for subscriber in subscribers:
        email = subscriber.get('email', '')
        user_id = subscriber.get('id')
        last_index = subscriber.get('last_word_index', 0)
        user_category = subscriber.get('preferred_category', 'ielts')

        if not email:
            continue

        try:
            # Get words (reuse existing logic from whatsapp_bot)
            words = whatsapp_bot.get_daily_words(10, last_index, category=user_category)

            if send_daily_vocab_email(subscriber, words):
                sent += 1
                # Update word index
                total_words = whatsapp_bot.get_vocabulary_count()
                new_index = (last_index + 10) % total_words if total_words > 0 else last_index + 10
                database.update_last_word_index(user_id, new_index)
                database.increment_leaderboard_words(user_id, 10)
                print(f"✓ Email sent to {email}")
            else:
                failed += 1
                print(f"✗ Email failed to {email}")

        except Exception as e:
            print(f"Error sending email to {email}: {e}")
            failed += 1

    print(f"Email broadcast complete: {sent} sent, {failed} failed")
    return {"sent": sent, "failed": failed, "total": len(subscribers)}
```

#### Step 1.6: Update Signup Form
**File:** `templates/signup.html`

Add delivery channel selection after the category dropdown:

```html
<!-- Delivery Channel -->
<div>
    <label class="block text-sm font-medium text-gray-700 mb-1">How do you want to receive words?</label>
    <select id="deliveryChannel" name="delivery_channel" required
        class="w-full px-3 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 text-gray-900 bg-gray-50">
        <option value="email">📧 Email (Free — Recommended)</option>
        <option value="whatsapp">💬 WhatsApp</option>
    </select>
    <p class="mt-1 text-xs text-gray-500">Email is free and unlimited. WhatsApp has limited slots.</p>
</div>
```

And update the JavaScript form submission to include `delivery_channel`.

#### Step 1.7: Add Dashboard Channel Selector
**File:** `templates/dashboard.html`

Add a new settings card in the dashboard allowing users to switch delivery channel:

```html
<!-- Delivery Channel Settings -->
<div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-6">
    <h3 class="text-base font-semibold text-gray-900 mb-2">📨 Delivery Channel</h3>
    <p class="text-sm text-gray-500 mb-3">Choose how you receive daily vocabulary</p>
    <select id="deliveryChannel" onchange="updateDeliveryChannel()" class="border rounded-lg px-3 py-2">
        <option value="email">📧 Email (Free)</option>
        <option value="whatsapp">💬 WhatsApp</option>
        <option value="both">📧 + 💬 Both</option>
    </select>
</div>
```

Add API endpoint `/api/update-delivery-channel` in `main.py`.

#### Step 1.8: Update `.env` with New Variables
**File:** `.env`

```env
# Email (Brevo - Free 300/day)
BREVO_SMTP_HOST=smtp-relay.sendinblue.com
BREVO_SMTP_PORT=587
BREVO_SENDER_EMAIL=your@email.com
BREVO_SENDER_NAME=VocabPro
BREVO_SMTP_LOGIN=your@email.com
BREVO_SMTP_PASSWORD=your-brevo-smtp-key

# Delivery Settings
DEFAULT_DELIVERY_CHANNEL=email
```

#### Step 1.9: Add Database Functions
**File:** `database.py`

```python
def get_users_by_time_and_channel(time: str, channel: str = None):
    """Get users scheduled for a specific time with optional channel filter"""
    conn = get_db_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    if channel:
        cursor.execute("""
            SELECT * FROM users
            WHERE preferred_time = %s
            AND is_subscribed = TRUE
            AND (is_paid = TRUE OR trial_ends > CURRENT_DATE)
            AND delivery_channel = %s
        """, (time, channel))
    else:
        cursor.execute("""
            SELECT * FROM users
            WHERE preferred_time = %s
            AND is_subscribed = TRUE
            AND (is_paid = TRUE OR trial_ends > CURRENT_DATE)
        """, (time,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [_row_to_dict(cursor, row) for row in rows]

def update_delivery_channel(user_id: int, channel: str):
    """Update user's delivery channel"""
    conn = get_db_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET delivery_channel = %s WHERE id = %s", (channel, user_id))
    conn.commit()
    cursor.close()
    conn.close()
    return True
```

---

## Implementation Roadmap

### Week 1: Email Infrastructure
| Task | Owner | Status |
|------|-------|--------|
| Sign up for Brevo | You | ⬜ |
| Verify email domain | You | ⬜ |
| Get SMTP credentials | You | ⬜ |
| Add env variables | AI | ⬜ |
| Create email_sender.py | AI | ⬜ |
| Add delivery_channel column | AI | ⬜ |
| Test email sending | Both | ⬜ |

### Week 2: Scheduler Integration
| Task | Owner | Status |
|------|-------|--------|
| Update scheduler for dual channel | AI | ⬜ |
| Update signup form with channel selector | AI | ⬜ |
| Add API endpoint for channel update | AI | ⬜ |
| Update dashboard with channel selector | AI | ⬜ |
| Test end-to-end flow | Both | ⬜ |

### Week 3: Migration & Rollout
| Task | Owner | Status |
|------|-------|--------|
| Migrate existing users to email channel | AI | ⬜ |
| Set default = email for new signups | AI | ⬜ |
| Monitor delivery success rates | You | ⬜ |
| Send test to all current users | You | ⬜ |

---

## Cost Analysis

### Before Email Feature
| Cost | Amount |
|------|--------|
| Green API Developer (3 chats) | $0 |
| Total | **$0/month** |

**Limitation:** Max 3 WhatsApp users → cannot scale

### After Email Feature
| Cost | Amount |
|------|--------|
| Green API Developer (3 chats) | $0 |
| Brevo SMTP | $0 |
| Total | **$0/month** |

**Advantage:** Unlimited email users + up to 3 WhatsApp users → **unlimited scalability**

### Brevo Free Tier Limits
| Metric | Limit | VocabPro Usage |
|--------|-------|----------------|
| Emails/day | 300 | 10 users × 1 = 10/day ✅ |
| Email forwarding | 2,000/month | 10 users × 30 = 300/month ✅ |
| Campaign emails | 500/month | Not used ✅ |

### Long-term Scaling (>300 emails/day)
When you exceed Brevo's free limit, upgrade options:
| Provider | Free Tier | Cost |
|---------|----------|------|
| Brevo | 300/day | Free |
| AWS SES | 62,000/month (1 year) | $0 (free tier) |
| Mailgun | 5,000/month | Free |
| SendGrid | 100/day | Free |

---

## User Experience Changes

### New User Signup Flow
```
1. Visit /signup
2. Fill name, email, phone, password
3. Select category (IELTS/GRE/Common)
4. NEW: Select delivery channel (Email ✅ recommended / WhatsApp)
5. Submit → Account created with email channel default
6. Redirected to dashboard
7. First email arrives at preferred_time
```

### Existing User Experience
```
1. Login to dashboard
2. See new "Delivery Channel" settings card
3. Can switch from WhatsApp → Email (or keep WhatsApp if < 3 users)
4. Email arrives at next scheduled time
```

### Email Appearance (What Users See)
```
Subject: 📚 Your Daily Vocabulary from VocabPro

From: VocabPro <your@email.com>

Body:
┌──────────────────────────────────────┐
│  📚 VocabPro                         │
│  Daily Vocabulary for Rahman         │
│                                      │
│  Hi Rahman, here are your 10 new     │
│  words for today!                    │
│                                      │
│  ┌──────────────────────────────┐    │
│  │ Aberration                  │    │
│  │ /ab-uh-RAY-shuhn            │    │
│  │ বিচ্যুতি                     │    │
│  │ "The aberration in the      │    │
│  │ data was corrected."         │    │
│  └──────────────────────────────┘    │
│  [ ... 9 more words ... ]            │
│                                      │
│  VocabPro — Learn 10 words daily     │
└──────────────────────────────────────┘
```

---

## Technical Architecture (Final State)

```
┌──────────────────────────────────────────────────────────┐
│                   VocabPro App                            │
│                                                          │
│  Request ──► FastAPI ──► Jinja2 Templates                 │
│                   │                                       │
│              Database                                    │
│         (PostgreSQL/SQLite)                              │
│                   │                                       │
│     ┌─────────────┼─────────────┐                          │
│     │             │             │                          │
│  Scheduler    API Routes   WebSocket (future)              │
│  (every 15m)                          │                  │
│     │                                       │              │
│  ┌──▼────────────────────────┐             │              │
│  │  get_users_by_time()      │             │              │
│  │  Split by delivery_channel │             │              │
│  └──┬─────────┬─────────────┘             │              │
│     │         │                           │              │
│  ┌──▼──┐   ┌──▼──────────────┐           │              │
│  │Email│   │ WhatsApp Bot    │           │              │
│  │Brevo│   │ (Green API)     │           │              │
│  │SMTP │   │ max 3 chats     │           │              │
│  └──┬──┘   └────┬────────────┘           │              │
│     │           │                              │          │
│  ┌──▼───┐   ┌───▼────┐                                   │
│  │User's│   │User's  │                                   │
│  │Email │   │WhatsApp│                                   │
│  └──────┘   └────────┘                                   │
└──────────────────────────────────────────────────────────┘
```

---

## What Happens to Existing WhatsApp Users?

### Migration Strategy
1. **Default all new signups** to `email` channel
2. **Existing WhatsApp users** keep their WhatsApp channel
3. **Display notice** in dashboard: "WhatsApp slots are limited. Consider switching to email for unlimited access."
4. **Soft migration** — let users choose to switch
5. **Green API chat count** tracked automatically (3-chat limit enforced by Green API, not your code)

### When Green API Blocks a Message
- Green API will return error 466 (chat limit exceeded)
- Log this error in your server logs
- Consider sending via email as fallback
- Notify user to switch to email channel

---

## Files to Modify/Create

| File | Action | Changes |
|------|--------|---------|
| `email_sender.py` | **CREATE** | New module for Brevo SMTP |
| `.env` | MODIFY | Add Brevo SMTP credentials |
| `database.py` | MODIFY | Add `delivery_channel` column, migration, functions |
| `main.py` | MODIFY | Update scheduler, add channel API endpoint |
| `templates/signup.html` | MODIFY | Add delivery channel dropdown |
| `templates/dashboard.html` | MODIFY | Add channel selector in settings |

| File | Action |
|------|--------|
| `requirements.txt` | MODIFY (add smtplib is stdlib — no new deps needed) |
| `email_feature_add.md` | THIS FILE |

---

## Dependencies

No new Python packages needed. All required modules are in Python's standard library:
- `smtplib` — for SMTP (stdlib)
- `email.mime.text` — for HTML emails (stdlib)
- `email.mime.multipart` — for email composition (stdlib)

External service: **Brevo** (free, no credit card needed)

---

## Security Notes

1. **SMTP credentials** — Store in `.env`, never commit to git
2. **Email sender** — Use a dedicated Brevo account's SMTP, not personal Gmail
3. **Rate limiting** — Brevo's free tier handles 300/day; add tracking if needed
4. **User emails** — Already in DB, no new PII collection needed
5. **TLS** — Use `starttls()` for encrypted SMTP connection (Brevo requires this)

---

## Testing Checklist

Before going live:

- [ ] Can send email from Python shell (smtplib test)
- [ ] Email arrives in inbox (not spam)
- [ ] HTML email renders correctly with Bengali text
- [ ] Scheduler sends email at correct time
- [ ] User can switch channel from dashboard
- [ ] New signup defaults to email channel
- [ ] Word index updates after email sent
- [ ] Leaderboard counters update after email sent
- [ ] Both channels work simultaneously (hybrid mode)

---

## Quick Start Guide (for you)

### Step 1: Sign up for Brevo (5 minutes)
1. Go to [brevo.com](https://brevo.com)
2. Click "Sign up free"
3. No credit card needed
4. Verify your email address

### Step 2: Get SMTP Credentials (3 minutes)
1. Go to Brevo Dashboard
2. SMTP & API → SMTP
3. Create a new SMTP key
4. Note down: Host, Port, Login, Password

### Step 3: Update `.env` (1 minute)
Add the Brevo credentials to your `.env` file

### Step 4: Deploy (AI will do this)
I'll implement the full email system once you have Brevo credentials.

---

## Expected Outcomes

| Metric | Before | After |
|--------|--------|-------|
| Max users | 3 (WhatsApp limit) | Unlimited (email) |
| Cost per user | $0 | $0 |
| Delivery method | WhatsApp only | Email + WhatsApp hybrid |
| User choice | None | Email or WhatsApp or Both |
| Scalability | ❌ Poor | ✅ Unlimited |
| Message cost | Meta per-message fees | $0 (Brevo free tier) |

---

## Rollback Plan

If email delivery fails:
1. Check Brevo dashboard for SMTP errors
2. Green API WhatsApp remains as backup for users with WhatsApp channel
3. Admin can force-all channel switch via admin panel
4. All word logic is in `whatsapp_bot.py` — email uses the same word-fetching functions, so content is always identical

---

*Document created: May 19, 2026*
*VocabPro - Email Feature Addition Plan*