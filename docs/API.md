# VocabPro - API Documentation

## Base URL
```
Production: https://your-app.onrender.com
Local: http://localhost:8000
```

---

## Authentication

### User Signup
```
POST /api/signup
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "01612345678",
  "password": "password123",
  "whatsapp": "01612345678",
  "preferred_category": "ielts"
}

Response:
{
  "status": "success",
  "message": "Account created! Check your WhatsApp for welcome message."
}
```

### User Login
```
POST /api/login
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "password123"
}

Response:
{
  "status": "success",
  "message": "Login successful",
  "redirect": "/dashboard"
}
```

### Forgot Password
```
POST /api/forgot-password
Content-Type: application/json

{
  "phone": "01612345678"
}

Response:
{
  "status": "success",
  "message": "Reset code sent to ****4567. Check your WhatsApp!"
}
```

### Reset Password
```
POST /api/reset-password
Content-Type: application/json

{
  "phone": "01612345678",
  "code": "123456",
  "new_password": "newpass123"
}

Response:
{
  "status": "success",
  "message": "Password reset successful! You can now login with your new password."
}
```

---

## User Endpoints (Requires Auth)

### Get Progress
```
GET /api/progress

Response:
{
  "status": "success",
  "progress": {
    "streak": 5,
    "total_words": 150,
    "words_sent": 50,
    "last_active": "2026-05-19"
  }
}
```

### Get Achievements
```
GET /api/achievements

Response:
{
  "status": "success",
  "achievements": [
    {"id": "first_word", "name": "🎯 First Word", "earned": true},
    {"id": "word_10", "name": "📖 Word Explorer", "earned": true}
  ]
}
```

### Update Preferred Time
```
POST /api/update-time
Content-Type: application/json

{
  "preferred_time": "09:30"
}

Response:
{
  "status": "success",
  "message": "Time updated to 09:30"
}
```

### Update Category
```
POST /api/update-category
Content-Type: application/json

{
  "preferred_category": "gre"
}

Response:
{
  "status": "success",
  "message": "Request submitted. Admin will review it soon."
}
```

---

## Quiz Endpoints

### Start Quiz
```
GET /api/quiz/start?type=bengali&source=learned

Response:
{
  "status": "success",
  "questions": [
    {
      "word": "Ubiquitous",
      "phonetic": "/yoo-BIK-wi-tuhs/",
      "correct": "সর্বত্র বিদ্যমান",
      "options": ["সর্বত্র বিদ্যমান", "ক্ষণস্থায়ী", "বাস্তবসম্মত", "দয়ালু"]
    }
  ],
  "type": "bengali"
}
```

### Submit Quiz
```
POST /api/quiz/submit
Content-Type: application/json

{
  "score": 8,
  "total": 10
}

Response:
{
  "status": "success",
  "score": 8,
  "total": 10,
  "percentage": 80,
  "high_score": 90,
  "new_badges": [],
  "new_record": false
}
```

---

## Contest Endpoints

### Get Current Contest
```
GET /api/contests/current

Response:
{
  "status": "success",
  "contest": {
    "id": 1,
    "name": "Weekly Challenge",
    "week": 20,
    "year": 2026,
    "status": "active",
    "time_remaining_seconds": 3600
  }
}
```

### Get Leaderboard
```
GET /api/contests/leaderboard

Response:
{
  "status": "success",
  "leaderboard": [
    {"rank": 1, "name": "User1", "score": 25},
    {"rank": 2, "name": "User2", "score": 23}
  ],
  "my_rank": {"rank": 5, "score": 18}
}
```

### Start Contest
```
POST /api/contests/1/start

Response:
{
  "status": "success",
  "message": "Quiz started",
  "question_count": 25,
  "time_remaining_seconds": 3600,
  "questions": [...]
}
```

### Submit Contest
```
POST /api/contests/1/submit
Content-Type: application/json

{
  "answers": {"1": "A", "2": "B", ...},
  "time_taken_seconds": 600
}

Response:
{
  "status": "success",
  "result": {
    "score": 20,
    "correct": 22,
    "wrong": 2,
    "skipped": 1,
    "time_seconds": 600
  }
}
```

---

## Chatbot Endpoints

### Send Message
```
POST /api/chatbot/send
Content-Type: application/json

{
  "message": "How do I use 'ubiquitous' in a sentence?",
  "persona": "tutor"
}

Response:
{
  "status": "success",
  "response": "You can use 'ubiquitous' like this: ...",
  "persona": "tutor"
}
```

### Get Chat History
```
GET /api/chatbot/history?persona=tutor

Response:
{
  "status": "success",
  "history": [
    {"role": "user", "content": "Hello", "created_at": "..."},
    {"role": "assistant", "content": "Hi! How can I help?"}
  ]
}
```

### Clear Chat
```
POST /api/chatbot/clear
Content-Type: application/json

{
  "persona": "tutor"
}

Response:
{
  "status": "success",
  "message": "Chat history cleared"
}
```

---

## Admin Endpoints

### Login
```
POST /api/admin/login
Content-Type: application/json

{
  "username": "admin",
  "password": "vocabpro123"
}

Response:
{
  "status": "success",
  "message": "Login successful"
}
```

### Get All Users
```
GET /api/admin/users?search=&status=all

Response:
{
  "status": "success",
  "users": [...]
}
```

### Approve Payment
```
POST /api/admin/approve-payment
Content-Type: application/json

{
  "payment_id": 1
}

Response:
{
  "status": "success",
  "message": "Payment approved"
}
```

### Generate Vocabulary
```
POST /api/admin/generate-vocabulary
Content-Type: application/json

{
  "count": 50,
  "category": "ielts"
}

Response:
{
  "status": "success",
  "message": "Generated 50 words, saved 48 to database"
}
```

### Import Words with AI
```
POST /api/admin/import-words-with-ai
Content-Type: multipart/form-data

file: [word list file]
category: "ielts"

Response:
{
  "status": "processing",
  "job_id": "abc123",
  "message": "Processing 100 words in background.",
  "total": 100,
  "new": 85
}
```

### Get Analytics
```
GET /api/admin/analytics

Response:
{
  "status": "success",
  "stats": {
    "total_users": 100,
    "active_subscribers": 50,
    "monthly_revenue": 750
  },
  "user_growth": [...],
  "activity": {...}
}
```

---

## Health Check Endpoints

### Health
```
GET /health

Response:
{
  "status": "ok",
  "message": "VocabPro is running!"
}
```

### Ping
```
GET /ping

Response:
{
  "status": "ok",
  "time": "2026-05-19T10:30:00"
}
```

---

## Error Responses

```json
{
  "status": "error",
  "message": "Error description here"
}
```

### Common Status Codes
- `401` - Not authenticated
- `400` - Bad request
- `404` - Not found
- `500` - Server error