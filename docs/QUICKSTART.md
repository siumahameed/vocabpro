# VocabPro - Quick Start Guide

## Prerequisites
- Python 3.9+
- Git
- Green API account (WhatsApp)
- OpenRouter account (AI)
- Groq account (Chatbot)

---

## Step 1: Local Setup

```bash
# Clone the project
git clone <your-repo-url>
cd vocabpro

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Or (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
copy .env.example .env

# Edit .env with your credentials
```

---

## Step 2: Configure Environment

Edit `.env` file:
```env
# Admin
ADMIN_USERNAME=admin
ADMIN_PASSWORD=vocabpro123

# Green API (Get from https://green-api.com)
GREEN_API_INSTANCE_ID=your_instance_id
GREEN_API_TOKEN=your_token

# Schedule
SCHEDULE_TIME=09:30

# AI APIs
OPENROUTER_API_KEY=your_key
GROQ_API_KEY=your_key
```

---

## Step 3: Run Locally

```bash
# Start the server
uvicorn main:app --reload

# Open browser
http://localhost:8000
```

---

## Step 4: Test Features

| Test | URL | Action |
|------|-----|--------|
| Landing Page | http://localhost:8000/ | Browse features |
| Sign Up | http://localhost:8000/signup | Create account |
| Login | http://localhost:8000/login | Test login |
| Dashboard | http://localhost:8000/dashboard | View stats |
| Admin Panel | http://localhost:8000/portal-manager-sium | Login with admin |

---

## Step 5: Configure WhatsApp

1. Go to [Green API Dashboard](https://green-api.com)
2. Get your Instance ID and Token
3. Update `.env` with credentials
4. Scan QR code with your WhatsApp
5. Test by sending a message!

---

## Common Issues

### ❌ "Module not found"
```bash
pip install -r requirements.txt
```

### ❌ "Database connection error"
- For local: SQLite is used automatically
- For production: Set DB_HOST environment variable

### ❌ "WhatsApp not sending"
- Check Green API credentials
- Ensure instance is active in Green API dashboard

### ❌ "AI not working"
- Verify OpenRouter API key
- Verify Groq API key

---

## Next Steps

1. Deploy to production (see DEPLOY.md)
2. Add vocabulary words via Admin Panel
3. Set up cron-job.org to keep app awake
4. Test daily vocabulary delivery
5. Launch! 🚀