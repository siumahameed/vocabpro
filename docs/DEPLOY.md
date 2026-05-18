# VocabPro - Deployment Guide

## 🚀 Deploy to Render (Free)

### Prerequisites
- [GitHub](https://github.com) account
- [Render](https://render.com) account (free)
- [cron-job.org](https://cron-job.org) account (free)

---

## Step 1: Prepare for Deployment

### 1.1 Ensure Files are Ready
- ✅ `requirements.txt` - Python dependencies
- ✅ `Procfile` - Render startup command
- ✅ `runtime.txt` - Python version
- ✅ `.env` - Environment variables (DO NOT COMMIT to GitHub)

### 1.2 Create .gitignore
```
__pycache__/
*.pyc
.env
*.db
*.sqlite
.vscode/
.idea/
```

### 1.3 Update .env for Production
```env
# Admin Credentials (CHANGE THESE!)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=vocabpro123

# Green API
GREEN_API_INSTANCE_ID=7107621945
GREEN_API_TOKEN=15571d94ece4499f9f117d2edb4282ceb063c9594be849fdb0

# Schedule
SCHEDULE_TIME=09:30

# AI APIs (Get from OpenRouter and Groq websites)
OPENROUTER_API_KEY=sk-or-v1-...
GROQ_API_KEY=gsk_...

# PostgreSQL (Will be provided by Render)
DB_HOST=...
DB_PORT=5432
DB_NAME=...
DB_USER=...
DB_PASSWORD=...
```

---

## Step 2: Deploy to Render

### 2.1 Push Code to GitHub
```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

### 2.2 Create PostgreSQL Database
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **New** → **PostgreSQL**
3. Configure:
   - **Name**: vocabpro-db
   - **Plan**: Free
   - **Region**: Virginia (or closest to you)
4. Click **Create Database**
5. Wait for it to provision (1-2 minutes)
6. **Copy the "Internal Database URL"** - you'll need this

### 2.3 Create Web Service
1. Click **New** → **Web Service**
2. Connect your GitHub repository
3. Configure:
   - **Name**: vocabpro
   - **Branch**: main
   - **Root Directory**: (leave empty)
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Click **Create Web Service**

### 2.4 Add Environment Variables
After creating the web service:
1. Go to **Environment** tab
2. Click **Add Environment Variable**
3. Add all variables from your `.env` file:
   ```
   DB_HOST = (from PostgreSQL connection string - part before colon)
   DB_PORT = 5432
   DB_NAME = (from connection string - after last /)
   DB_USER = (from connection string - after //)
   DB_PASSWORD = (from connection string - after :)
   
   ADMIN_USERNAME = admin
   ADMIN_PASSWORD = vocabpro123
   GREEN_API_INSTANCE_ID = 7107621945
   GREEN_API_TOKEN = your_token
   SCHEDULE_TIME = 09:30
   OPENROUTER_API_KEY = your_key
   GROQ_API_KEY = your_key
   ```
4. Click **Deploy**

---

## Step 3: Keep App Awake (Important!)

Render's free tier sleeps after 15 minutes of inactivity. Use cron-job.org to keep it awake:

### 3.1 Setup cron-job.org
1. Go to [cron-job.org](https://cron-job.org)
2. Create account → Click **Create Cronjob**
3. Configure:
   - **Title**: VocabPro Health Check
   - **URL**: `https://your-app-name.onrender.com/health`
   - **Schedule**: Every 10 minutes
4. Click **Create**

### 3.2 Alternative: UptimeRobot
1. Go to [uptimerobot.com](https://uptimerobot.com)
2. Create account → **Add New Monitor**
3. Configure:
   - **Type**: HTTPS
   - **URL**: `https://your-app-name.onrender.com/health`
   - **Interval**: 10 minutes

---

## Step 4: Verify Deployment

| Check | URL |
|-------|-----|
| App loads | `https://your-app.onrender.com` |
| Health check | `https://your-app.onrender.com/health` |
| Login page | `https://your-app.onrender.com/login` |
| Admin panel | `https://your-app.onrender.com/portal-manager-sium` |

---

## Step 5: Post-Deployment Checklist

- [ ] Test user registration
- [ ] Verify welcome message via WhatsApp
- [ ] Check daily vocabulary delivery timing
- [ ] Test admin login and panel access
- [ ] Add vocabulary words via admin panel
- [ ] Verify database connection working

---

## 🔧 Troubleshooting

### App won't start
- Check logs in Render dashboard
- Verify all environment variables are set
- Ensure `requirements.txt` has all dependencies

### Database connection error
- Verify DB_HOST is correct (don't include port)
- Ensure PostgreSQL is fully provisioned
- Check DB_NAME, DB_USER, DB_PASSWORD

### WhatsApp not working
- Check Green API credentials in dashboard
- Ensure instance is active (not expired)
- Try sending test message via Green API dashboard

### App goes to sleep
- Ensure cron-job.org is pinging every 10 minutes
- Check cron-job.org execution history

---

## 📋 Render Free Tier Limits

| Resource | Limit |
|----------|-------|
| Compute | 750 hours/month |
| Sleep | After 15 min inactivity |
| Storage | 1GB |
| Database | 1GB |

**Tip**: Use cron-job.org to ping every 10 min to prevent sleep!

---

## 🔄 Update Deployment

To update after code changes:
1. Push changes to GitHub
2. Render auto-deploys on push to main branch
3. Or manually trigger deploy in Render dashboard

---

<p align="center">
  <strong>Deployment Complete! 🎉</strong>
</p>