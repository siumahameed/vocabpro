# VocabPro - WhatsApp Vocabulary SaaS

<p align="center">
  <img src="https://img.shields.io/badge/Version-2.1-blue" alt="Version">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/Platform-Render-yellow" alt="Platform">
</p>

## 📱 Overview

**VocabPro** is a WhatsApp-based English vocabulary learning SaaS platform for Bengali speakers in Bangladesh. Users receive 10 vocabulary words daily via WhatsApp with Bengali meanings, phonetics, and examples.

---

## 🎯 Key Features

| Feature | Description |
|---------|-------------|
| 📅 **Daily Vocabulary** | 10 words delivered daily at user's preferred time |
| 🤖 **AI Chatbot** | Interactive practice with 6 personas (tutor, mentor, IELTS examiner, etc.) |
| 📊 **Progress Tracking** | Streaks, words learned, achievements, leaderboards |
| 🏆 **Weekly Contests** | Quiz competitions with rankings |
| 💳 **Payment System** | bKash integration for subscriptions (15 Taka/month) |
| 📚 **Categories** | IELTS, GRE, Common English words |
| 👥 **Referral System** | Earn free months by referring friends |
| ⚙️ **Admin Panel** | Full control over users, payments, vocabulary |

---

## 🛠 Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL (production) / SQLite (local)
- **WhatsApp**: Green API
- **AI**: OpenRouter (vocabulary generation), Groq (chatbot)
- **Frontend**: HTML, JavaScript, Tailwind CSS
- **Hosting**: Render (Free tier)

---

## 📁 Project Structure

```
vocabpro/
├── main.py              # FastAPI app & routes
├── database.py          # Database models & functions
├── whatsapp_bot.py      # WhatsApp messaging & AI
├── requirements.txt     # Python dependencies
├── Procfile            # Render deployment config
├── runtime.txt         # Python version
├── .env                # Environment variables
├── static/             # CSS & JS files
│   ├── style.css
│   └── app.js
├── templates/          # HTML templates
│   ├── index.html
│   ├── dashboard.html
│   ├── admin.html
│   └── ...
└── docs/               # Documentation
    ├── README.md
    ├── DEPLOY.md
    ├── API.md
    └── QUICKSTART.md
```

---

## 🚀 Quick Start

### Local Development

```bash
# Clone & setup
git clone <repo>
cd vocabpro

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run the app
uvicorn main:app --reload

# Open browser
http://localhost:8000
```

### Deploy to Production

See [DEPLOY.md](DEPLOY.md) for detailed deployment instructions.

---

## 🔑 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DB_HOST` | PostgreSQL host | Production |
| `DB_PORT` | PostgreSQL port (5432) | Production |
| `DB_NAME` | Database name | Production |
| `DB_USER` | Database username | Production |
| `DB_PASSWORD` | Database password | Production |
| `ADMIN_USERNAME` | Admin login username | ✅ Yes |
| `ADMIN_PASSWORD` | Admin login password | ✅ Yes |
| `GREEN_API_INSTANCE_ID` | Green API instance ID | ✅ Yes |
| `GREEN_API_TOKEN` | Green API token | ✅ Yes |
| `OPENROUTER_API_KEY` | OpenRouter API key (AI) | ✅ Yes |
| `GROQ_API_KEY` | Groq API key (Chatbot) | ✅ Yes |
| `SCHEDULE_TIME` | Default delivery time (09:30) | Optional |

---

## 📄 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Landing page |
| `/signup` | GET/POST | User registration |
| `/login` | GET/POST | User login |
| `/dashboard` | GET | User dashboard |
| `/payment` | GET/POST | Payment page |
| `/api/signup` | POST | Register new user |
| `/api/login` | POST | User login |
| `/api/get-words` | POST | Get vocabulary (removed) |
| `/api/quiz/start` | GET | Start quiz |
| `/api/quiz/submit` | POST | Submit quiz |
| `/api/contests/current` | GET | Get current contest |
| `/api/chatbot/send` | POST | Send to AI chatbot |
| `/portal-manager-sium` | GET | Admin panel |
| `/api/admin/*` | POST | Admin endpoints |

---

## 💰 Pricing

- **Free Trial**: 7 days
- **Monthly Subscription**: 15 Taka/month via bKash
- **Referral Reward**: 1 free month per 3 referrals

---

## 📞 Support

- WhatsApp: Contact via VocabPro chatbot
- Email: (add your email)

---

## 📝 License

MIT License - See LICENSE file for details.

---

<p align="center">
  Made with ❤️ by <strong>Sium</strong>
</p>