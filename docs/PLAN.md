===============================================================================
                    VOCABPRO - COMPLETE PROJECT DOCUMENTATION
===============================================================================

PROJECT: WhatsApp Vocabulary Subscription Service (SaaS)
TARGET: Students and language learners in Bangladesh
VERSION: 2.1 (Unlimited Vocabulary)
LAST UPDATED: May 2026

===============================================================================
1. PROJECT OVERVIEW
===============================================================================

App Name: VocabPro
Tagline: "Daily English Vocabulary via WhatsApp"
Owner: Sium
Price: 15 Taka/month (after 7-day free trial)
bKash: 01608872616

Mission: Help Bangladesh students learn English vocabulary daily via WhatsApp

===============================================================================
2. TECHNICAL ARCHITECTURE
===============================================================================

Backend: FastAPI (Python)
Database: PostgreSQL (production) | SQLite (development)
WhatsApp: Green API
Frontend: HTML + JavaScript + Tailwind CSS
Hosting: Render (Free tier)
Keep Awake: cron-job.org (ping every 10 minutes)

===============================================================================
3. FEATURES IMPLEMENTED
===============================================================================

✅ User Registration & Login
✅ User Dashboard
✅ Payment System (bKash Manual)
✅ Admin Panel (/portal-manager-sium)
✅ WhatsApp Bot (Green API)
✅ Daily Vocabulary at Preferred Time
✅ Word Rotation (each user gets different words)
✅ Anti-Spam Protection (2-5 sec delay)
✅ Referral System
✅ Statistics & Progress Tracking
✅ Health Endpoints (/health, /ping)
✅ PostgreSQL Database
✅ Enhanced Vocabulary Format (Phonetic + Bengali)
✅ UNLIMITED Vocabulary (Gemini API + Database)

===============================================================================
4. DATABASE SCHEMA (POSTGRESQL)
===============================================================================

USERS TABLE:
- id (SERIAL PRIMARY KEY)
- name (TEXT)
- email (TEXT UNIQUE)
- phone (TEXT UNIQUE)
- password_hash (TEXT)
- whatsapp_number (TEXT)
- is_subscribed (BOOLEAN DEFAULT FALSE)
- trial_ends (DATE)
- is_paid (BOOLEAN DEFAULT FALSE)
- paid_date (DATE)
- is_admin (BOOLEAN DEFAULT FALSE)
- timezone (TEXT DEFAULT 'Asia/Dhaka')
- preferred_time (TEXT DEFAULT '09:30')  -- morning/evening option
- last_word_index (INTEGER DEFAULT 0)  -- for word rotation
- words_learned (INTEGER DEFAULT 0)  -- progress tracking
- referral_code (TEXT UNIQUE)  -- unique referral code
- referred_by (INTEGER)  -- who referred this user
- referral_count (INTEGER DEFAULT 0)  -- how many referred
- free_months_earned (INTEGER DEFAULT 0)  -- free months from referrals
- created_at (TIMESTAMP)

PAYMENTS TABLE:
- id (SERIAL PRIMARY KEY)
- user_id (INTEGER REFERENCES users(id))
- amount (INTEGER)
- transaction_id (TEXT)
- status (TEXT: pending/approved/rejected)
- verified_by (TEXT)
- verified_at (TIMESTAMP)
- created_at (TIMESTAMP)

VOCABULARY TABLE:
- id (SERIAL PRIMARY KEY)
- word (TEXT)
- meaning_bn (TEXT)
- example (TEXT)
- category (TEXT)

===============================================================================
5. VOCABULARY FORMAT (ENHANCED)
===============================================================================

Message Format:
📚 Daily Vocabulary - VocabPro
━━━━━━━━━━━━━━━━━━━━━━

1. *Ubiquitous*
   🔊 [yoo-BIK-wi-tuhs]
   🇧🇩 সর্বত্র বিদ্যমান
   📝 "Smartphones have become ubiquitous in modern society."

━━━━━━━━━━━━━━━━━━━━━━
⏰ Daily at 09:30
💡 Practice makes perfect!

Current Vocabulary: 60+ words with phonetic pronunciation (fallback)
Unlimited: Generated via Gemini API and stored in PostgreSQL
Categories: IELTS, GRE, General English

HOW IT WORKS:
1. Words stored in PostgreSQL vocabulary table
2. Daily messages pull from database (no API cost)
3. Gemini API used ONCE to generate words
4. After generation, no API calls needed for daily messages

===============================================================================
6. OPENROUTER API FOR VOCABULARY GENERATION
===============================================================================

OpenRouter (Free Models):
- Primary: google/gemma-4-31b-it:free
- Secondary: meta-llama/llama-3.2-3b-instruct:free
- Tertiary: openai/gpt-oss-120b:free

How to Use:
1. Get API key: https://openrouter.ai
2. Add to environment: OPENROUTER_API_KEY=your_key
3. Call: POST /api/admin/generate-vocabulary
   Body: {"count": 50}
4. Words saved to PostgreSQL automatically

Flow:
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Gemini API   │───▶│  50+ Words      │───▶│  PostgreSQL     │
│   (One time)   │    │  with Bengali   │    │  vocabulary table│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                    │
                                                    ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Scheduler     │◀───│  Pull from DB   │◀───│  Daily Messages │
│   (Daily)       │    │  (No API cost)  │    │  (Free forever!)│
└─────────────────┘    └─────────────────┘    └─────────────────┘

Code Location:
- whatsapp_bot.py: generate_vocabulary()
- main.py: /api/admin/generate-vocabulary
- database.py: add_vocabulary_word(), get_vocabulary_words()

===============================================================================
6. REFERRAL SYSTEM
===============================================================================

How it works:
- Each user gets unique referral code
- User shares code with friends
- Friend signs up with referral code
- After 3 referrals, user gets 1 month free

Promotion: "Refer 3 friends, get 1 month free!"

Database fields:
- referral_code: 8-character unique code
- referred_by: ID of user who referred
- referral_count: number of successful referrals
- free_months_earned: months earned through referrals

===============================================================================
7. STATISTICS & PROGRESS
===============================================================================

User Dashboard Shows:
- Words learned count
- Current position (percentile rank)
- Referral count
- Free months earned
- Subscription status

Example: "You have learned 70 words—you are in the top 10% of learners!"

===============================================================================
8. TIME PREFERENCE
===============================================================================

User Options:
- 🌅 Morning (9:30 AM)
- 🌙 Evening (9:00 PM)

Scheduler:
- Runs every hour
- Checks user preferred_time
- Sends to users at their chosen time
- Word rotation based on last_word_index

===============================================================================
9. SECURITY FEATURES
===============================================================================

Anti-Spam:
- 2-5 second random delay between messages
- Word order variation
- Logging for each message

Admin URL:
- Old: /admin
- New: /portal-manager-sium (hidden from public)

Environment Variables:
- DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
- ADMIN_USERNAME, ADMIN_PASSWORD
- GREEN_API_INSTANCE_ID, GREEN_API_TOKEN
- OPENROUTER_API_KEY (for vocabulary generation)
- GROQ_API_KEY (for chatbot)
- SCHEDULE_TIME, SECRET_KEY

===============================================================================
10. ENDPOINTS
===============================================================================

Public Routes:
- / (Landing Page - SEO Optimized)
- /login
- /signup
- /health (for cron-job.org)
- /ping (for monitoring)

Protected Routes:
- /dashboard
- /payment
- /portal-manager-sium (Admin)

API Endpoints:
- /api/signup
- /api/login
- /api/submit-payment
- /api/get-words
- /api/update-time
- /api/admin/generate-vocabulary (generate via Gemini)
- /api/admin/vocabulary-count (check word count)
- /api/admin/* (protected)

===============================================================================
11. FILE STRUCTURE
===============================================================================

vocabpro/
├── main.py              # FastAPI app with all routes
├── database.py          # PostgreSQL database
├── whatsapp_bot.py      # Green API + vocabulary
├── requirements.txt     # Python packages
├── Procfile            # Render deployment
├── runtime.txt        # Python version
├── env.example         # Environment template
├── DEPLOY.md          # Deployment guide
├── static/
│   ├── app.js         # JavaScript
│   └── style.css      # Styles
└── templates/
    ├── base.html       # Layout
    ├── index.html      # Landing
    ├── login.html      # Login
    ├── signup.html    # Sign up
    ├── dashboard.html # User dashboard
    ├── payment.html   # Payment
    └── admin.html     # Admin panel

===============================================================================
12. DEPLOYMENT INSTRUCTIONS
===============================================================================

1. Create GitHub repo and upload all files

2. Create Render account:
   - Add PostgreSQL database (free)
   - Create Web Service
   - Connect GitHub repo

3. Set Environment Variables:
   DB_HOST=your_postgres_host
   DB_PORT=5432
   DB_NAME=vocabpro
   DB_USER=postgres
   DB_PASSWORD=your_password
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=your_password
   GREEN_API_INSTANCE_ID=7107621945
   GREEN_API_TOKEN=15571d94ece4499f9f117d2edb4282ceb063c9594be849fdb0
   SCHEDULE_TIME=09:30
   OPENROUTER_API_KEY=your_openrouter_api_key
   GROQ_API_KEY=your_groq_api_key

4. Deploy:
   Start command: gunicorn main:app --workers 2 --bind 0.0.0.0:$PORT

5. Keep Awake (Important!):
   - Go to https://cron-job.org
   - Create cron job
   - URL: https://your-app.onrender.com/health
   - Schedule: Every 10 minutes

===============================================================================
13. ADMIN ACCESS
===============================================================================

URL: https://your-app.onrender.com/portal-manager-sium

Features:
- View all users
- Approve/reject payments
- Broadcast messages
- View statistics
- Manage subscriptions
- Generate unlimited vocabulary (Gemini API)
- View vocabulary count

===============================================================================
14. WHATSAPP BOT COMMANDS
===============================================================================

Users can send:
- JOIN / SUBSCRIBE → Subscribe
- STOP / UNSUBSCRIBE → Unsubscribe
- VOCAB → Get words now
- STATUS → Check subscription
- HELP → Show commands
- TIME → Show schedule

Auto-responses:
- Welcome message on signup
- Payment confirmation
- Trial reminder

===============================================================================
15. SUCCESS METRICS
===============================================================================

Month 1 Targets:
- Signups: 100 users
- Paid subscribers: 50 users
- Revenue: 750 Taka (50 x 15)
- Daily active: 80%

===============================================================================
16. GROWTH STRATEGIES
===============================================================================

1. Referral Program:
   - "Refer 3 friends, get 1 month free"
   - Track via referral_code and referred_by

2. Word-of-Mouth:
   - Students share with friends
   - Natural growth in Bangladesh

3. Quality Content:
   - Phonetic pronunciation helps pronunciation
   - Bengali meanings help understanding

===============================================================================
17. FUTURE IMPROVEMENTS (OPTIONAL)
===============================================================================

- Quiz feature for progress tracking
- Multiple vocabulary categories
- Leaderboard
- badges system
- API access for developers

===============================================================================
18. QUICK START CHECKLIST
===============================================================================

□ Upload to GitHub
□ Deploy on Render with PostgreSQL
□ Set environment variables (OPENROUTER_API_KEY, GROQ_API_KEY, etc.)
□ Configure cron-job.org
□ Test /portal-manager-sium admin
□ Test user signup and login
□ Generate vocabulary: POST /api/admin/generate-vocabulary
□ Test WhatsApp message delivery
□ Launch!

===============================================================================
19. SUPPORT
===============================================================================

For issues:
- Check Render logs
- Verify PostgreSQL connection
- Check Green API status
- Verify Gemini API key is set
- Verify cron-job.org is running
- Check vocabulary count: GET /api/admin/vocabulary-count

===============================================================================
                              END OF DOCUMENTATION
===============================================================================