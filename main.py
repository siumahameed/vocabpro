"""
VocabPro - FastAPI Main Application
Complete SaaS Platform with WhatsApp Integration
"""

import os
import csv
import io
from dotenv import load_dotenv

# Load .env file from current directory
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(env_path)

import schedule
import time
from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from contextlib import asynccontextmanager
from starlette.middleware.sessions import SessionMiddleware
import uvicorn
from jinja2 import Environment, FileSystemLoader

SECRET_KEY = os.environ.get("SESSION_SECRET_KEY", "vocabpro-secret-key-change-in-production")

# Jinja2 environment for rendering templates
jinja_env = Environment(loader=FileSystemLoader("templates"), autoescape=True)

# Helper function to render templates directly
def render_page(template_name: str, context: dict):
    # Inject logged_in state into all templates
    request = context.get("request")
    context["logged_in"] = request.session.get("user_id") is not None if request else False
    template = jinja_env.get_template(template_name)
    return template.render(**context)

# Import modules
import database
import whatsapp_bot

# Initialize database
database.init_db()
database.init_contest_tables()
database.migrate_contest_fields()

# ==================== CONFIGURATION ====================

SEO_CONFIG = {
    "title": "VocabPro - Daily English Vocabulary via WhatsApp",
    "description": "Learn 10 new English words every day with Bengali meanings. Perfect for IELTS, GRE & Language Learners in Bangladesh.",
    "keywords": "vocabulary, english learning, whatsapp, bangladesh, ielts, gre, daily words",
    "author": "Sium",
    "og_title": "VocabPro - Learn English via WhatsApp",
    "og_description": "10 new vocabulary words daily with Bengali meanings. Start free!",
    "og_url": "https://vocabpro.com",
    "og_image": "/static/logo.png"
}

# Admin credentials (in production, use environment variables)
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "vocabpro123")

# ==================== APP SETUP ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Start scheduler - runs every 15 minutes to catch custom time preferences
    schedule.every(15).minutes.do(send_daily_vocabulary)
    print("Scheduler started - Checking every 15 minutes for users")
    yield

app = FastAPI(title="VocabPro", lifespan=lifespan)

# Session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="vocabpro_session",
    https_only=True,
    same_site="lax"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Security
security = HTTPBasic()

# ==================== DEPENDENCIES ====================

def get_current_user(request: Request) -> Optional[dict]:
    """Get current user from session"""
    user_id = request.session.get("user_id")
    if user_id:
        return database.get_user_by_id(user_id)
    return None

def require_auth(user: Optional[dict] = Depends(get_current_user)):
    """Require user authentication"""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

def require_admin(credentials: HTTPBasicCredentials = Depends(security)):
    """Require admin authentication"""
    if credentials.username != ADMIN_USERNAME or credentials.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return True

def get_current_admin(request: Request) -> bool:
    """Check if admin is logged in via session"""
    return request.session.get("is_admin", False)

def require_admin_session(request: Request, admin: bool = Depends(get_current_admin)):
    """Require admin authentication via session"""
    if not admin:
        # If it's an API call, return 401. If it's a page visit, redirect to login
        if request.url.path.startswith("/api/"):
            raise HTTPException(status_code=401, detail="Not authenticated")
        return RedirectResponse("/admin-login", status_code=302)
    return True

# ==================== PYDANTIC MODELS ====================

class UserSignup(BaseModel):
    name: str
    email: str
    phone: str
    password: str
    whatsapp: str
    preferred_category: str = "ielts"

class UserLogin(BaseModel):
    email: str
    password: str

class PaymentSubmit(BaseModel):
    transaction_id: str
    sender_phone: str

class TimeUpdate(BaseModel):
    preferred_time: str

class CategoryUpdate(BaseModel):
    preferred_category: str

VALID_CATEGORIES = ["ielts", "gre", "common"]

# ==================== ROUTES ====================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Landing Page - SEO Optimized"""
    html = render_page("index.html", {
        "request": request,
        "seo_title": SEO_CONFIG["title"],
        "seo_description": SEO_CONFIG["description"],
        "seo_keywords": SEO_CONFIG["keywords"],
        "seo_author": SEO_CONFIG["author"],
        "seo_og_title": SEO_CONFIG["og_title"],
        "seo_og_description": SEO_CONFIG["og_description"],
        "seo_og_url": SEO_CONFIG["og_url"],
        "seo_og_image": SEO_CONFIG["og_image"],
        "page": "home"
    })
    return HTMLResponse(content=html)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login Page"""
    user = get_current_user(request)
    if user:
        return RedirectResponse("/dashboard")
    html = render_page("login.html", {"request": request, "seo_title": "Login - VocabPro", "seo_description": SEO_CONFIG["description"], "page": "login"})
    return HTMLResponse(content=html)

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    """Registration Page"""
    user = get_current_user(request)
    if user:
        return RedirectResponse("/dashboard")
    html = render_page("signup.html", {"request": request, "seo_title": "Sign Up - VocabPro", "seo_description": SEO_CONFIG["description"], "page": "signup"})
    return HTMLResponse(content=html)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user: dict = Depends(require_auth)):
    """User Dashboard"""
    days_left = 0
    if user.get("trial_ends"):
        trial_end = user["trial_ends"]
        if isinstance(trial_end, str):
            trial_end = datetime.strptime(trial_end, "%Y-%m-%d").date()
        days_left = (trial_end - datetime.now().date()).days
    html = render_page("dashboard.html", {"request": request, "seo_title": "Dashboard - VocabPro", "seo_description": SEO_CONFIG["description"], "user": user, "days_left": max(0, days_left)})
    return HTMLResponse(content=html)

@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request, user: dict = Depends(require_auth)):
    """User Profile Page"""
    html = render_page("profile.html", {"request": request, "seo_title": "Profile - VocabPro", "seo_description": SEO_CONFIG["description"], "user": user})
    return HTMLResponse(content=html)

@app.post("/api/profile/update")
async def update_profile(data: dict, user: dict = Depends(require_auth)):
    """Update user profile"""
    name = data.get("name", "").strip()
    phone = data.get("phone", "").strip()
    whatsapp_number = data.get("whatsapp_number", "").strip()
    preferred_time = data.get("preferred_time", "09:30")
    timezone = data.get("timezone", "Asia/Dhaka")
    
    if not name:
        return {"status": "error", "message": "Name is required"}
    
    if not phone or not whatsapp_number:
        return {"status": "error", "message": "Phone and WhatsApp number are required"}
    
    success = database.update_user_profile(user["id"], {
        "name": name,
        "phone": phone,
        "whatsapp_number": whatsapp_number,
        "preferred_time": preferred_time,
        "timezone": timezone
    })
    
    if success:
        return {"status": "success", "message": "Profile updated successfully!"}
    return {"status": "error", "message": "Failed to update profile"}

@app.post("/api/profile/change-password")
async def change_password(data: dict, user: dict = Depends(require_auth)):
    """Change user password"""
    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")
    
    if not current_password or not new_password:
        return {"status": "error", "message": "Current and new password are required"}
    
    user_data = database.get_user_by_id(user["id"])
    if not user_data:
        return {"status": "error", "message": "User not found"}
    
    import hashlib
    current_hash = hashlib.sha256(current_password.encode()).hexdigest()
    
    if current_hash != user_data.get("password_hash"):
        return {"status": "error", "message": "Current password is incorrect"}
    
    new_hash = hashlib.sha256(new_password.encode()).hexdigest()
    success = database.update_password(user["id"], new_hash)
    
    if success:
        return {"status": "success", "message": "Password changed successfully!"}
    return {"status": "error", "message": "Failed to change password"}

@app.get("/api/progress")
async def get_progress(user: dict = Depends(require_auth)):
    """Get user progress data"""
    progress = database.get_user_progress(user["id"])
    return {"status": "success", "progress": progress}

@app.get("/api/achievements")
async def get_achievements(user: dict = Depends(require_auth)):
    """Get user achievements"""
    achievements = database.get_user_achievements(user["id"])
    return {"status": "success", "achievements": achievements}

@app.get("/payment", response_class=HTMLResponse)
async def payment_page(request: Request, user: dict = Depends(require_auth)):
    """Payment Page"""
    html = render_page("payment.html", {"request": request, "seo_title": "Payment - VocabPro", "seo_description": SEO_CONFIG["description"], "user": user})
    return HTMLResponse(content=html)

@app.get("/admin-login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """Admin Login Page"""
    if request.session.get("is_admin"):
        return RedirectResponse("/portal-manager-sium")
    html = render_page("admin-login.html", {"request": request, "seo_title": "Admin Login - VocabPro", "seo_description": SEO_CONFIG["description"]})
    return HTMLResponse(content=html)

@app.post("/api/admin/login")
async def admin_login(request: Request, data: dict):
    """Admin Login API - accepts admin env creds OR any admin user from DB"""
    username = data.get("username", "")
    password = data.get("password", "")

    # Check env-based admin credentials first
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        request.session["is_admin"] = True
        request.session["admin_user"] = username
        return {"status": "success", "message": "Login successful"}

    # Check database admin users (email + password)
    user = database.verify_user(username, password)
    if user and user.get("is_admin"):
        request.session["is_admin"] = True
        request.session["admin_user"] = user["email"]
        return {"status": "success", "message": "Login successful"}

    return {"status": "error", "message": "Invalid username or password"}

@app.get("/portal-manager-sium", response_class=HTMLResponse)
async def admin_page(request: Request, _: bool = Depends(require_admin_session)):
    """Admin Panel"""
    if not request.session.get("is_admin"):
        return RedirectResponse("/admin-login")
    users = database.get_all_users()
    payments = database.get_pending_payments()
    stats = database.get_stats()
    vocabulary = database.get_all_vocabulary()
    html = render_page("admin.html", {"request": request, "seo_title": "Admin - VocabPro", "seo_description": SEO_CONFIG["description"], "users": users, "payments": payments, "stats": stats, "vocabulary": vocabulary})
    return HTMLResponse(content=html)

@app.get("/admin-logout")
async def admin_logout(request: Request):
    """Admin Logout"""
    request.session.pop("is_admin", None)
    request.session.pop("admin_user", None)
    return RedirectResponse("/admin-login")

# Health check endpoint for cron-job.org
@app.get("/health")
async def health_check():
    """Health check endpoint - ping this to keep app awake"""
    return {"status": "ok", "message": "VocabPro is running!"}

@app.get("/ping")
async def ping():
    """Simple ping endpoint for cron job"""
    return {"status": "ok", "time": datetime.now().isoformat()}

@app.get("/logout")
async def logout(request: Request):
    """Logout"""
    request.session.clear()
    return RedirectResponse("/")

@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    """Forgot Password Page"""
    html = render_page("forgot-password.html", {"request": request, "seo_title": "Forgot Password - VocabPro", "seo_description": SEO_CONFIG["description"]})
    return HTMLResponse(content=html)

@app.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request):
    """Reset Password Page"""
    html = render_page("reset-password.html", {"request": request, "seo_title": "Reset Password - VocabPro", "seo_description": SEO_CONFIG["description"]})
    return HTMLResponse(content=html)

import asyncio
import concurrent.futures
import secrets

@app.post("/api/forgot-password")
async def forgot_password(data: dict):
    """Forgot Password API - Send reset code via WhatsApp"""
    import random
    
    phone = data.get("phone", "").strip()
    
    if not phone:
        return {"status": "error", "message": "WhatsApp number is required"}
    
    # Find user by WhatsApp number
    conn = database.get_db_connection()
    if not conn:
        return {"status": "error", "message": "Database error"}
    
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE whatsapp_number = ?", (phone,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        return {"status": "error", "message": "No account found with this WhatsApp number"}
    
    user = dict(user)
    
    # Generate 6-digit reset code
    reset_code = ''.join(secrets.choice('0123456789') for _ in range(6))

    # Store code in database (expires in 30 minutes)
    from datetime import datetime, timedelta
    expires_at = (datetime.now() + timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
    whatsapp_number = user.get("whatsapp_number", "")

    if not database.store_reset_code(whatsapp_number, reset_code, expires_at):
        return {"status": "error", "message": "Failed to generate reset code"}

    # Create reset message
    message = f"""🔐 VocabPro Password Reset

Your password reset code is: *{reset_code}*

Use this code to reset your password.
Code expires in 30 minutes.

If you didn't request this, ignore this message."""

    # Send via WhatsApp
    if whatsapp_number:
        whatsapp_bot.send_whatsapp_message(whatsapp_number, message)

    return {
        "status": "success",
        "message": f"Reset code sent to {whatsapp_number[-4:]}****. Check your WhatsApp!"
    }

@app.post("/api/reset-password")
async def reset_password(data: dict):
    """Reset Password API"""
    phone = data.get("phone", "").strip()
    code = data.get("code", "").strip()
    new_password = data.get("new_password", "")

    if not phone or not code or not new_password:
        return {"status": "error", "message": "All fields are required"}

    if len(new_password) < 6:
        return {"status": "error", "message": "Password must be at least 6 characters"}

    # Verify the reset code
    if not database.verify_reset_code(phone, code):
        return {"status": "error", "message": "Invalid or expired reset code. Please request a new one."}

    # Reset password
    import hashlib
    password_hash = hashlib.sha256(new_password.encode()).hexdigest()

    conn = database.get_db_connection()
    if not conn:
        return {"status": "error", "message": "Database error"}

    cursor = conn.cursor()
    try:
        if database.USE_POSTGRES:
            cursor.execute("UPDATE users SET password_hash = %s WHERE whatsapp_number = %s", (password_hash, phone))
        else:
            cursor.execute("UPDATE users SET password_hash = ? WHERE whatsapp_number = ?", (password_hash, phone))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    # Clear the reset code so it can't be reused
    database.clear_reset_code(phone)

    return {"status": "success", "message": "Password reset successful! You can now login with your new password."}

# ==================== API ENDPOINTS ====================

@app.post("/api/signup")
async def signup(user: UserSignup):
    """Handle user registration"""
    # Check if email exists
    if database.get_user_by_email(user.email):
        return {"status": "error", "message": "Email already registered"}
    
    # Create user
    category = user.preferred_category if user.preferred_category in VALID_CATEGORIES else "ielts"
    user_id = database.create_user(
        name=user.name,
        email=user.email,
        phone=user.phone,
        password=user.password,
        whatsapp=user.whatsapp,
        preferred_category=category
    )
    
    if not user_id:
        return {"status": "error", "message": "Failed to create account"}
    
    # Send welcome message
    whatsapp_bot.send_welcome_to_user(user.whatsapp, user.name)
    
    return {"status": "success", "message": "Account created! Check your WhatsApp for welcome message."}

@app.post("/api/login")
async def login(user: UserLogin, request: Request):
    """Handle user login"""
    verified_user = database.verify_user(user.email, user.password)

    if not verified_user:
        return {"status": "error", "message": "Invalid email or password"}
    
    # Set session
    request.session["user_id"] = verified_user["id"]

    return {"status": "success", "message": "Login successful", "redirect": "/dashboard"}

@app.post("/api/submit-payment")
async def submit_payment(payment: PaymentSubmit, user: dict = Depends(require_auth)):
    """Submit payment for verification"""
    # Create payment
    payment_id = database.create_payment(
        user_id=user["id"],
        amount=15,
        transaction_id=payment.transaction_id
    )
    
    if not payment_id:
        return {"status": "error", "message": "Failed to submit payment"}
    
    return {
        "status": "success",
        "message": "Payment submitted for verification. You'll be notified once verified (usually within 24 hours)."
    }

@app.post("/api/get-words")
async def get_words_now(user: dict = Depends(require_auth)):
    """Send vocabulary words immediately"""
    if not user.get("is_subscribed"):
        return {"status": "error", "message": "Subscribe to get words"}
    
    user_category = user.get("preferred_category", "ielts")
    words = whatsapp_bot.get_daily_words(category=user_category)
    message = whatsapp_bot.create_vocabulary_message(words)
    
    success = whatsapp_bot.send_whatsapp_message(user["whatsapp_number"], message)
    
    if success:
        return {"status": "success", "message": "Words sent to your WhatsApp!"}
    return {"status": "error", "message": "Failed to send words. Please try again."}

@app.post("/api/update-time")
async def update_preferred_time(data: TimeUpdate, user: dict = Depends(require_auth)):
    """Update user's preferred message time"""
    # Validate time format (HH:MM)
    import re
    if not re.match(r'^(?:[1-9]|1[0-9]|2[0-3]):[0-5][0-9]$', data.preferred_time):
        return {"status": "error", "message": "Invalid time format"}
    
    hour = int(data.preferred_time.split(':')[0])
    minute = int(data.preferred_time.split(':')[1])
    
    # Allow times from 11:00 (11 AM) to 23:00 (11 PM)
    if hour < 11 or hour >= 23:
        return {"status": "error", "message": "Time must be between 11:00 AM and 11:00 PM"}
    
    success = database.update_preferred_time(user["id"], data.preferred_time)
    
    if success:
        return {"status": "success", "message": f"Time updated to {data.preferred_time}"}
    return {"status": "error", "message": "Failed to update time"}

@app.post("/api/update-category")
async def update_preferred_category(data: CategoryUpdate, user: dict = Depends(require_auth)):
    """Request category change (admin approval required, max 2 requests/month)"""
    if data.preferred_category not in VALID_CATEGORIES:
        return {"status": "error", "message": "Invalid category"}
    if data.preferred_category == user.get("preferred_category"):
        return {"status": "error", "message": "You are already in this category."}
    result = database.create_category_request(user["id"], data.preferred_category)
    if result["success"]:
        return {"status": "success", "message": result["message"]}
    return {"status": "error", "message": result["message"]}

@app.get("/api/admin/category-requests")
async def get_category_requests(_: bool = Depends(require_admin_session)):
    """Get pending category change requests"""
    requests = database.get_pending_category_requests()
    return {"status": "success", "requests": requests}

@app.post("/api/admin/approve-category-request")
async def approve_category_request(data: dict, request: Request, _: bool = Depends(require_admin_session)):
    """Approve a category change request"""
    request_id = data.get("request_id")
    if not request_id:
        return {"status": "error", "message": "Missing request_id"}
    admin_user = request.session.get("admin_user", "admin")
    success = database.approve_category_request(request_id, admin_user)
    if success:
        return {"status": "success", "message": "Category change approved"}
    return {"status": "error", "message": "Request not found or already resolved"}

@app.post("/api/admin/reject-category-request")
async def reject_category_request(data: dict, request: Request, _: bool = Depends(require_admin_session)):
    """Reject a category change request"""
    request_id = data.get("request_id")
    if not request_id:
        return {"status": "error", "message": "Missing request_id"}
    admin_user = request.session.get("admin_user", "admin")
    success = database.reject_category_request(request_id, admin_user)
    if success:
        return {"status": "success", "message": "Request rejected"}
    return {"status": "error", "message": "Request not found or already resolved"}

# ==================== QUIZ API ENDPOINTS ====================

import random as _random

@app.get("/api/quiz/start")
async def start_quiz(request: Request, type: str = "bengali", source: str = "learned", user: dict = Depends(require_auth)):
    """Start a quiz with random multiple-choice questions"""
    category = user.get("preferred_category", "")

    if source == "random":
        # Random words from all vocabulary
        words = database.get_learned_words(user["id"], None, count=10, use_user_category=False)
    else:
        # Learned words from user's category
        words = database.get_learned_words(user["id"], category, count=10)
        # If not enough learned words, supplement with random from any category
        if len(words) < 5:
            extra = database.get_learned_words(user["id"], None, count=10 - len(words), use_user_category=False)
            existing_ids = {w["id"] for w in words}
            for w in extra:
                if w["id"] not in existing_ids:
                    words.append(w)
                    if len(words) >= 10:
                        break

    if len(words) < 2:
        return {"status": "error", "message": "Not enough words available. Need at least 2 words."}

    questions = []
    for w in words:
        # Get 3 wrong options for Bengali meanings - try category first, then any
        wrong_meanings = database.get_wrong_options(w["id"], category, count=3)
        if len(wrong_meanings) < 3:
            wrong_meanings += database.get_wrong_options(w["id"], None, count=3 - len(wrong_meanings))
        if len(wrong_meanings) < 3:
            continue

        # Get 3 wrong English words - try category first, then any
        wrong_words = database.get_wrong_english_words(w["id"], category, count=3)
        if len(wrong_words) < 3:
            wrong_words += database.get_wrong_english_words(w["id"], None, count=3 - len(wrong_words))
        if len(wrong_words) < 3:
            continue

        bengali_options = [w["meaning_bn"]] + wrong_meanings[:3]
        _random.shuffle(bengali_options)

        english_options = [w["word"]] + wrong_words[:3]
        _random.shuffle(english_options)

        questions.append({
            "word": w["word"],
            "phonetic": w.get("phonetic", ""),
            "correct": w["meaning_bn"],
            "options": bengali_options,
            "english_options": english_options
        })

    if len(questions) < 1:
        return {"status": "error", "message": "Not enough words for a quiz. Add more words to your category."}

    return {"status": "success", "questions": questions[:10], "type": type}


@app.get("/contest/{contest_id}", response_class=HTMLResponse)
async def contest_page(request: Request, contest_id: int, user: dict = Depends(require_auth)):
    """Weekly Contest Quiz Page"""
    contest = database.get_contest_by_id(contest_id)
    if not contest:
        return RedirectResponse("/dashboard?error=contest_not_found")
    
    html = render_page("contest.html", {
        "request": request,
        "seo_title": "Weekly Challenge - VocabPro",
        "seo_description": SEO_CONFIG["description"],
        "contest": contest,
        "user": user
    })
    return HTMLResponse(content=html)

@app.post("/api/quiz/submit")
async def submit_quiz(data: dict, request: Request, user: dict = Depends(require_auth)):
    """Submit quiz score and update high score"""
    score = data.get("score", 0)
    total = data.get("total", 10)

    if total == 0:
        return {"status": "error", "message": "Invalid quiz data"}

    percentage = round((score / total) * 100)

    # Update high score
    result = database.update_quiz_score(user["id"], percentage)

    # Check and award achievements
    new_badges = database.check_and_award_achievements(user["id"])

    return {
        "status": "success",
        "score": score,
        "total": total,
        "percentage": percentage,
        "high_score": result.get("high_score", percentage),
        "new_badges": [{"name": b["name"], "icon": b["icon"]} for b in new_badges] if new_badges else [],
        "new_record": result.get("new_record", False)
    }

# ==================== ADMIN API ENDPOINTS ====================

@app.post("/api/admin/approve-payment")
async def approve_payment(data: dict, _: bool = Depends(require_admin_session)):
    """Approve payment and activate subscription"""
    payment_id = data.get("payment_id")
    if not payment_id:
        return {"status": "error", "message": "Payment ID required"}
    
    database.approve_payment(payment_id, ADMIN_USERNAME)
    
    # Send confirmation to user
    # (In production, get user info and send WhatsApp)
    
    return {"status": "success", "message": "Payment approved"}

@app.post("/api/admin/reject-payment")
async def reject_payment(data: dict, _: bool = Depends(require_admin_session)):
    """Reject payment"""
    payment_id = data.get("payment_id")
    if not payment_id:
        return {"status": "error", "message": "Payment ID required"}
    
    database.reject_payment(payment_id)
    return {"status": "success", "message": "Payment rejected"}

@app.post("/api/admin/toggle-subscription")
async def toggle_subscription(data: dict, _: bool = Depends(require_admin_session)):
    """Toggle user subscription"""
    user_id = data.get("user_id")
    if not user_id:
        return {"status": "error", "message": "User ID required"}
    
    user = database.get_user_by_id(user_id)
    if not user:
        return {"status": "error", "message": "User not found"}
    
    # Toggle
    new_status = not user.get("is_paid", False)
    database.update_user_subscription(user_id, new_status)
    
    return {"status": "success", "message": f"Subscription {'activated' if new_status else 'deactivated'}"}

@app.post("/api/admin/broadcast")
async def broadcast(data: dict, _: bool = Depends(require_admin_session)):
    """Send message to all users"""
    message = data.get("message")
    if not message:
        return {"status": "error", "message": "Message required"}
    
    # Get all active users
    users = database.get_all_subscribers()
    
    sent = 0
    failed = 0
    
    for user in users:
        if whatsapp_bot.send_whatsapp_message(user["whatsapp_number"], message):
            sent += 1
        else:
            failed += 1
    
    return {"status": "success", "message": f"Sent to {sent} users", "sent": sent, "failed": failed}

@app.post("/api/admin/generate-vocabulary")
async def generate_vocabulary(data: dict, _: bool = Depends(require_admin_session)):
    """Generate vocabulary using OpenRouter AI and save to database"""
    count = data.get("count", 50)
    category = data.get("category", None)

    result = whatsapp_bot.generate_vocabulary(count, category)

    if result.get("success"):
        cat_label = f" ({category})" if category else ""
        return {
            "status": "success",
            "message": f"Generated {result.get('generated')}{cat_label} words, saved {result.get('saved')} to database",
            "generated": result.get("generated"),
            "saved": result.get("saved")
        }
    else:
        return {"status": "error", "message": result.get("error", "Unknown error")}

@app.post("/api/admin/clear-vocabulary")
async def clear_vocabulary(_: bool = Depends(require_admin_session)):
    """Delete all vocabulary words from the database"""
    success = database.clear_all_vocabulary()
    if success:
        return {"status": "success", "message": "All vocabulary words deleted"}
    return {"status": "error", "message": "Failed to clear vocabulary"}

@app.get("/api/admin/vocabulary-count")
async def get_vocabulary_count(_: bool = Depends(require_admin_session)):
    """Get vocabulary count from database"""
    count = whatsapp_bot.get_vocabulary_count()
    return {"status": "success", "count": count}

@app.post("/api/admin/import-words-with-ai")
async def import_words_with_ai(request: Request, _: bool = Depends(require_admin_session)):
    """Import a word list (TXT/CSV/Excel) with background AI enrichment. Returns job_id immediately."""
    from fastapi.responses import JSONResponse
    import io

    try:
        form = await request.form()
        file = form.get("file")
        category = form.get("category", "general")

        if not file:
            return JSONResponse({"status": "error", "message": "No file uploaded"})

        filename = file.filename.lower()
        content = await file.read()

        words = []

        if filename.endswith(('.xlsx', '.xls')):
            try:
                import openpyxl
                wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True)
                ws = wb.active
                for row in ws.iter_rows(max_col=1, values_only=True):
                    cell = row[0]
                    if cell:
                        word = str(cell).strip()
                        if word and len(word) > 1 and word.lower() not in ["word", "english", "vocabulary", "words"]:
                            words.append(word)
                wb.close()
            except Exception as e:
                return JSONResponse({"status": "error", "message": f"Error reading Excel file: {str(e)}"})
        else:
            text = content.decode("utf-8", errors="ignore")
            for line in text.splitlines():
                for part in line.split(","):
                    word = part.strip().strip('"').strip("'")
                    if word and len(word) > 1 and word.lower() not in ["word", "english", "vocabulary", "words"]:
                        words.append(word)

        if not words:
            return JSONResponse({"status": "error", "message": "No words found in file"})

        # Remove duplicates (case-insensitive)
        seen = set()
        unique_words = []
        for w in words:
            key = w.lower()
            if key not in seen:
                seen.add(key)
                unique_words.append(w)

        # Skip words already in database
        existing = database.get_existing_words(unique_words)
        new_words = [w for w in unique_words if w.lower() not in existing]

        if not new_words:
            return JSONResponse({"status": "success", "message": f"All {len(words)} words already exist.", "total": len(words), "saved": 0, "skipped": len(words)})

        # Start background job and return immediately
        job_id = whatsapp_bot.create_import_job(new_words, category)

        return JSONResponse({
            "status": "processing",
            "job_id": job_id,
            "message": f"Processing {len(new_words)} words in background.",
            "total": len(words),
            "new": len(new_words)
        })
    except Exception as e:
        print(f"Import error: {e}")
        return JSONResponse({"status": "error", "message": f"Import failed: {str(e)}"}, status_code=500)

@app.get("/api/admin/import-status/{job_id}")
async def get_import_status(job_id: str, _: bool = Depends(require_admin_session)):
    """Poll import job progress"""
    status = whatsapp_bot.get_job_status(job_id)

    if status.get("status") == "not_found":
        return {"status": "error", "message": "Job not found"}

    return {
        "status": status["status"],
        "percentage": status.get("percentage", 0),
        "processed": status.get("processed", 0),
        "total": status.get("total", 0),
        "saved": status.get("saved", 0),
        "failed": status.get("failed", 0),
        "errors": status.get("errors", [])
    }

@app.post("/api/admin/import-cancel/{job_id}")
async def cancel_import(job_id: str, _: bool = Depends(require_admin_session)):
    """Cancel a running import job"""
    success = whatsapp_bot.cancel_import_job(job_id)
    if success:
        return {"status": "success", "message": "Job cancelled"}
    return {"status": "error", "message": "Job not found or already completed"}

# ==================== ADMIN: ENHANCED USER MANAGEMENT ====================

@app.get("/api/admin/users")
async def admin_search_users(search: str = "", status: str = "all", _: bool = Depends(require_admin_session)):
    """Search and filter users"""
    users = database.search_users(search, status)
    return {"status": "success", "users": users}

@app.get("/api/admin/user/{user_id}")
async def admin_get_user(user_id: int, _: bool = Depends(require_admin_session)):
    """Get user details"""
    user = database.get_user_detail(user_id)
    if not user:
        return {"status": "error", "message": "User not found"}
    return {"status": "success", "user": user}

@app.post("/api/admin/delete-user")
async def admin_delete_user(data: dict, _: bool = Depends(require_admin_session)):
    """Delete a user"""
    user_id = data.get("user_id")
    if not user_id:
        return {"status": "error", "message": "User ID required"}
    success = database.delete_user(user_id)
    if success:
        return {"status": "success", "message": "User deleted"}
    return {"status": "error", "message": "Failed to delete user"}

@app.post("/api/admin/bulk-toggle")
async def admin_bulk_toggle(data: dict, _: bool = Depends(require_admin_session)):
    """Bulk activate/deactivate users"""
    user_ids = data.get("user_ids", [])
    action = data.get("action", "activate")
    if not user_ids:
        return {"status": "error", "message": "No users selected"}
    count = database.bulk_toggle_subscription(user_ids, action)
    return {"status": "success", "message": f"{count} users updated", "count": count}

@app.get("/api/admin/export-users")
async def admin_export_users(_: bool = Depends(require_admin_session)):
    """Export users as CSV"""
    from fastapi.responses import StreamingResponse
    import csv
    import io

    users = database.search_users()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Name", "Email", "Phone", "WhatsApp", "Status", "Trial Ends", "Streak", "Words Learned", "Joined"])
    for u in users:
        writer.writerow([
            u["id"], u["name"], u["email"], u["phone"], u.get("whatsapp_number", ""),
            "Paid" if u["is_paid"] else "Trial", u.get("trial_ends", ""),
            u.get("streak_days", 0), u.get("words_learned", 0), u.get("created_at", "")[:10]
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=users.csv"}
    )

# ==================== ADMIN: ENHANCED PAYMENT MANAGEMENT ====================

@app.get("/api/admin/payments")
async def admin_get_payments(status: str = "all", _: bool = Depends(require_admin_session)):
    """Get all payments with filter"""
    payments = database.get_all_payments(status)
    revenue = database.get_revenue_stats()
    return {"status": "success", "payments": payments, "revenue": revenue}

# ==================== ADMIN: ENHANCED VOCABULARY MANAGEMENT ====================

@app.get("/api/admin/vocabulary")
async def admin_search_vocabulary(search: str = "", category: str = "all", _: bool = Depends(require_admin_session)):
    """Search and filter vocabulary"""
    words = database.search_vocabulary(search, category)
    return {"status": "success", "vocabulary": words}

@app.post("/api/admin/add-word")
async def admin_add_word(data: dict, _: bool = Depends(require_admin_session)):
    """Add a new vocabulary word"""
    word = data.get("word", "").strip()
    meaning_bn = data.get("meaning_bn", "").strip()
    example = data.get("example", "").strip()
    category = data.get("category", "general").strip()
    phonetic = data.get("phonetic", "").strip()

    if not word or not meaning_bn:
        return {"status": "error", "message": "Word and Bengali meaning are required"}

    success = database.add_vocabulary_word(word, meaning_bn, example, category, phonetic)
    if success:
        return {"status": "success", "message": "Word added"}
    return {"status": "error", "message": "Failed to add word (may already exist)"}

@app.post("/api/admin/update-word")
async def admin_update_word(data: dict, _: bool = Depends(require_admin_session)):
    """Update an existing vocabulary word"""
    word_id = data.get("word_id")
    word = data.get("word", "").strip()
    meaning_bn = data.get("meaning_bn", "").strip()
    example = data.get("example", "").strip()
    category = data.get("category", "general").strip()
    phonetic = data.get("phonetic", "").strip()

    if not word_id or not word or not meaning_bn:
        return {"status": "error", "message": "Word ID, word, and meaning are required"}

    success = database.update_vocabulary_word(word_id, word, meaning_bn, example, category, phonetic)
    if success:
        return {"status": "success", "message": "Word updated"}
    return {"status": "error", "message": "Failed to update word"}

@app.post("/api/admin/delete-word")
async def admin_delete_word(data: dict, _: bool = Depends(require_admin_session)):
    """Delete a vocabulary word"""
    word_id = data.get("word_id")
    if not word_id:
        return {"status": "error", "message": "Word ID required"}
    success = database.delete_vocabulary_word(word_id)
    if success:
        return {"status": "success", "message": "Word deleted"}
    return {"status": "error", "message": "Failed to delete word"}

@app.post("/api/admin/import-vocabulary")
async def admin_import_vocabulary(request: Request, _: bool = Depends(require_admin_session)):
    """Import vocabulary from CSV"""
    from fastapi.responses import JSONResponse

    form = await request.form()
    file = form.get("file")

    if not file:
        return {"status": "error", "message": "No file uploaded"}

    content = await file.read()
    text = content.decode("utf-8")
    reader = csv.reader(io.StringIO(text))

    imported = 0
    skipped = 0
    for i, row in enumerate(reader):
        if i == 0 and row[0].lower() in ["word", "english"]:
            continue  # Skip header
        if len(row) >= 2:
            word = row[0].strip()
            meaning = row[1].strip()
            example = row[2].strip() if len(row) > 2 else ""
            category = row[3].strip() if len(row) > 3 else "general"
            phonetic = row[4].strip() if len(row) > 4 else ""
            if database.add_vocabulary_word(word, meaning, example, category, phonetic):
                imported += 1
            else:
                skipped += 1

    return {"status": "success", "message": f"Imported {imported} words, skipped {skipped}", "imported": imported, "skipped": skipped}

# ==================== ADMIN: ANALYTICS ====================

@app.get("/api/admin/analytics")
async def admin_analytics(_: bool = Depends(require_admin_session)):
    """Get all analytics data"""
    stats = database.get_stats()
    user_growth = database.get_user_growth(30)
    activity = database.get_activity_stats()
    delivery = database.get_delivery_stats()
    top_users = database.get_top_users(10)
    vocab_categories = database.get_vocab_category_stats()

    return {
        "status": "success",
        "stats": stats,
        "user_growth": user_growth,
        "activity": activity,
        "delivery": delivery,
        "top_users": top_users,
        "vocab_categories": vocab_categories
    }

# ==================== WEEKLY QUIZ CONTEST ENDPOINTS ====================

@app.get("/api/contests/current")
async def get_current_contest_info(request: Request):
    """Get today's daily contest (auto-creates if needed) with live leaderboard"""
    contest = database.ensure_daily_contest()
    if not contest:
        return {"status": "success", "contest": None, "message": "No active contest"}

    leaderboard = database.get_live_leaderboard(contest["id"], limit=5)

    # Check if current user has participated
    user_id = request.session.get("user_id")
    user_participated = False
    user_rank_info = None
    if user_id:
        participation = database.check_user_participation(user_id, contest["id"])
        if participation:
            user_participated = True
            user_rank_info = database.get_user_contest_rank(user_id, contest["id"])

    return {
        "status": "success",
        "contest": {
            "id": contest["id"],
            "name": contest["name"],
            "question_count": contest["question_count"],
            "status": "active",
            "user_participated": user_participated,
            "user_rank": user_rank_info
        },
        "leaderboard": leaderboard
    }


@app.get("/api/contests/today-leaderboard")
async def get_today_leaderboard():
    """Get live leaderboard for today's contest (no auth required)"""
    contest = database.ensure_daily_contest()
    if not contest:
        return {"status": "success", "leaderboard": [], "contest": None}

    leaderboard = database.get_live_leaderboard(contest["id"], limit=10)

    return {
        "status": "success",
        "contest": {"id": contest["id"], "name": contest["name"]},
        "leaderboard": leaderboard
    }


@app.get("/api/contests/weekly")
async def get_weekly_contest(request: Request):
    """Get this week's Friday contest info"""
    contest = database.ensure_weekly_contest()
    if not contest:
        return {"status": "success", "contest": None, "message": "No weekly contest available"}

    leaderboard = database.get_live_leaderboard(contest["id"], limit=5)

    user_id = request.session.get("user_id")
    user_participated = False
    user_rank_info = None
    if user_id:
        participation = database.check_user_participation(user_id, contest["id"])
        if participation:
            user_participated = True
            user_rank_info = database.get_user_contest_rank(user_id, contest["id"])

    return {
        "status": "success",
        "contest": {
            "id": contest["id"],
            "name": contest["name"],
            "question_count": contest["question_count"],
            "time_per_question_seconds": contest.get("time_per_question_seconds", 15),
            "status": contest.get("status", "active"),
            "user_participated": user_participated,
            "user_rank": user_rank_info
        },
        "leaderboard": leaderboard
    }


@app.get("/api/contests/leaderboard")
async def get_contest_leaderboard(user: dict = Depends(require_auth)):
    """Get the latest completed contest leaderboard"""
    contest = database.get_completed_contest()
    if not contest:
        return {"status": "success", "leaderboard": [], "message": "No completed contest"}
    
    leaderboard = database.get_contest_leaderboard(contest["id"])
    user_rank = database.get_user_contest_rank(user["id"], contest["id"])
    
    return {
        "status": "success",
        "contest": {
            "id": contest["id"],
            "name": contest["name"],
            "status": contest["status"],
            "revealed_at": contest["reveal_time"]
        },
        "leaderboard": leaderboard,
        "my_rank": user_rank
    }


@app.get("/api/contests/history")
async def get_user_contest_history(user: dict = Depends(require_auth)):
    """Get user's contest participation history"""
    history = database.get_user_contest_history(user["id"])
    return {"status": "success", "history": history}


@app.get("/api/contests/{contest_id}")
async def get_contest_details(contest_id: int, user: dict = Depends(require_auth)):
    """Get contest details and user's participation status"""
    contest = database.get_contest_by_id(contest_id)
    if not contest:
        return {"status": "error", "message": "Contest not found"}
    
    participation = database.check_user_participation(user["id"], contest_id)
    
    import datetime
    now = datetime.datetime.now()
    start_time = datetime.datetime.fromisoformat(contest["start_time"])
    end_time = datetime.datetime.fromisoformat(contest["end_time"])
    
    if now < start_time:
        contest_status = "upcoming"
    elif now < end_time:
        contest_status = "active"
    else:
        contest_status = "completed"
    
    return {
        "status": "success",
        "contest": {
            "id": contest["id"],
            "name": contest["name"],
            "start_time": contest["start_time"],
            "end_time": contest["end_time"],
            "question_count": contest["question_count"],
            "status": contest_status
        },
        "participated": participation is not None,
        "participation": participation
    }


@app.post("/api/contests/{contest_id}/start")
async def start_contest(contest_id: int, user: dict = Depends(require_auth)):
    """Start a contest - returns questions if eligible"""
    contest = database.get_contest_by_id(contest_id)
    if not contest:
        return {"status": "error", "message": "Contest not found"}

    existing = database.check_user_participation(user["id"], contest_id)
    if existing:
        return {"status": "error", "message": "You have already participated in this contest"}

    questions = database.shuffle_contest_questions(contest_id)
    if not questions:
        # Regenerate questions if missing
        result = database.generate_contest_questions(contest_id, 25)
        if result.get("success"):
            questions = database.shuffle_contest_questions(contest_id)
        if not questions:
            return {"status": "error", "message": "No questions available"}

    quiz_questions = []
    for q in questions:
        qtype = q.get("question_type", "")
        if qtype == "en_to_bn":
            question_text = q["word"]
            meaning_text = q["word"]
        else:
            question_text = q.get("correct_answer", q["word"])
            meaning_text = q["word"]
        quiz_questions.append({
            "number": q["question_number"],
            "type": qtype,
            "question": question_text,
            "meaning_for_type": meaning_text,
            "options": q.get("options", []),
            "phonetic": q.get("phonetic", "")
        })

    time_per_q = contest.get("time_per_question_seconds", 0) or 0
    contest_type = contest.get("contest_type", "daily")
    total_time = time_per_q * len(quiz_questions) if time_per_q > 0 else 1800
    total_time = max(total_time, 1800)  # minimum 30 min

    return {
        "status": "success",
        "message": "Quiz started",
        "contest_id": contest_id,
        "contest_type": contest_type,
        "question_count": len(quiz_questions),
        "time_limit_seconds": total_time,
        "time_per_question_seconds": time_per_q,
        "questions": quiz_questions
    }


@app.post("/api/contests/{contest_id}/submit")
async def submit_contest(contest_id: int, data: dict, user: dict = Depends(require_auth)):
    """Submit contest answers with live ranking"""
    contest = database.get_contest_by_id(contest_id)
    if not contest:
        return {"status": "error", "message": "Contest not found"}

    existing = database.check_user_participation(user["id"], contest_id)
    if existing:
        return {"status": "error", "message": "You have already participated"}

    answers = data.get("answers", {})
    time_taken = data.get("time_taken_seconds", 0)
    timeouts = data.get("timeouts", 0)

    questions = database.get_contest_questions(contest_id)
    question_map = {str(q["question_number"]): q for q in questions}

    correct_count = 0
    wrong_count = 0
    skipped_count = 0

    for q_num, q_data in question_map.items():
        user_answer = answers.get(q_num, "").strip()

        if not user_answer or user_answer == "timeout":
            skipped_count += 1
        elif user_answer == q_data["correct_answer"]:
            correct_count += 1
        else:
            wrong_count += 1

    # For weekly contest: skipped = 0 points, correct = +1, wrong = -1
    # For daily contest: same formula
    score = correct_count - wrong_count
    submitted_at = datetime.now().isoformat()

    success = database.save_contest_participation(
        user_id=user["id"],
        contest_id=contest_id,
        score=score,
        correct_count=correct_count,
        wrong_count=wrong_count,
        skipped_count=skipped_count,
        time_taken_seconds=time_taken,
        submitted_at=submitted_at
    )

    if not success:
        return {"status": "error", "message": "Failed to save participation"}

    # Get live rank after auto-ranking
    rank_info = database.get_user_contest_rank(user["id"], contest_id)
    leaderboard = database.get_live_leaderboard(contest_id, limit=5)

    return {
        "status": "success",
        "message": "Quiz submitted successfully!",
        "result": {
            "score": score,
            "correct": correct_count,
            "wrong": wrong_count,
            "skipped": skipped_count,
            "time_seconds": time_taken,
            "rank": rank_info,
            "leaderboard": leaderboard
        }
    }


@app.get("/api/contests/{contest_id}/my-rank")
async def get_my_contest_rank(contest_id: int, user: dict = Depends(require_auth)):
    """Get user's rank in a specific contest"""
    contest = database.get_contest_by_id(contest_id)
    if not contest:
        return {"status": "error", "message": "Contest not found"}
    
    if contest["status"] != "completed":
        return {"status": "error", "message": "Contest not completed yet"}
    
    rank_data = database.get_user_contest_rank(user["id"], contest_id)
    if not rank_data:
        return {"status": "success", "participated": False, "message": "You did not participate"}
    
    return {"status": "success", "participated": True, "rank": rank_data}


# ==================== ADMIN: CONTEST MANAGEMENT ====================

@app.post("/api/admin/contest/create")
async def admin_create_contest(data: dict, _: bool = Depends(require_admin_session)):
    """Create a new quiz contest"""
    name = data.get("name", "")
    question_count = data.get("question_count", 25)
    
    if not name:
        return {"status": "error", "message": "Contest name is required"}
    
    import datetime
    today = datetime.datetime.now()
    
    contest_id = database.create_contest(
        name=name,
        week_number=today.isocalendar()[1],
        year=today.year,
        start_time=data.get("start_time", today.isoformat()),
        end_time=data.get("end_time", (today + datetime.timedelta(days=1)).isoformat()),
        reveal_time=data.get("reveal_time", (today + datetime.timedelta(days=1)).isoformat()),
        question_count=question_count
    )
    
    if not contest_id:
        return {"status": "error", "message": "Failed to create contest"}
    
    return {"status": "success", "message": "Contest created", "contest_id": contest_id}


@app.post("/api/admin/contest/{contest_id}/generate")
async def admin_generate_questions(contest_id: int, _: bool = Depends(require_admin_session)):
    """Generate questions for a contest"""
    contest = database.get_contest_by_id(contest_id)
    if not contest:
        return {"status": "error", "message": "Contest not found"}
    
    result = database.generate_contest_questions(contest_id, contest["question_count"])
    
    if result.get("success"):
        return {"status": "success", "message": f"Generated {result.get('generated')} questions"}
    return {"status": "error", "message": result.get("error", "Generation failed")}


@app.get("/api/admin/contest/{contest_id}/results")
async def admin_get_contest_results(contest_id: int, _: bool = Depends(require_admin_session)):
    """Get full results of a contest"""
    contest = database.get_contest_by_id(contest_id)
    if not contest:
        return {"status": "error", "message": "Contest not found"}
    
    leaderboard = database.get_contest_leaderboard(contest_id, 500)
    
    return {
        "status": "success",
        "contest": contest,
        "leaderboard": leaderboard,
        "total_participants": len(leaderboard)
    }


@app.post("/api/admin/contest/{contest_id}/reveal")
async def admin_reveal_leaderboard(contest_id: int, _: bool = Depends(require_admin_session)):
    """Reveal contest leaderboard and notify winners"""
    contest = database.get_contest_by_id(contest_id)
    if not contest:
        return {"status": "error", "message": "Contest not found"}
    
    database.calculate_and_save_ranks(contest_id)
    database.update_contest_status(contest_id, "completed")
    
    winners = database.get_top_5_winners(contest_id)
    notified = 0
    
    for winner in winners:
        message = whatsapp_bot.create_contest_winner_message(winner, contest["name"])
        if whatsapp_bot.send_whatsapp_message(winner["whatsapp"], message):
            notified += 1
    
    return {
        "status": "success",
        "message": f"Leaderboard revealed, notified {notified}/5 winners"
    }


@app.post("/api/admin/contest/{contest_id}/activate")
async def admin_activate_contest(contest_id: int, _: bool = Depends(require_admin_session)):
    """Activate a contest"""
    success = database.update_contest_status(contest_id, "active")
    if success:
        return {"status": "success", "message": "Contest activated"}
    return {"status": "error", "message": "Failed to activate contest"}


# ==================== LEADERBOARD ENDPOINTS ====================

@app.get("/api/leaderboard")
async def get_leaderboard(type: str = "weekly", user: dict = Depends(require_auth)):
    """Get leaderboard rankings"""
    if type not in ["daily", "weekly", "monthly", "streak", "all_time"]:
        type = "weekly"

    if type == "daily":
        # Daily contest leaderboard
        contest = database.ensure_daily_contest()
        if not contest:
            return {"status": "success", "leaderboard": [], "user_rank": {"rank": 0, "value": 0}, "type": "daily"}
        leaderboard = database.get_live_leaderboard(contest["id"], limit=100)
        user_rank_info = database.get_user_contest_rank(user["id"], contest["id"])
        return {
            "status": "success",
            "leaderboard": [{"rank": e["rank"], "user_id": e["user_id"], "name": e["name"], "value": e["score"]} for e in leaderboard],
            "user_rank": user_rank_info or {"rank": 0, "value": 0},
            "type": "daily"
        }

    leaderboard = database.get_leaderboard(type, limit=100)
    user_ranks = database.get_user_leaderboard_rank(user["id"])

    return {
        "status": "success",
        "leaderboard": leaderboard,
        "user_rank": user_ranks.get(type, {"rank": 0, "value": 0}),
        "type": type
    }


# ==================== CHATBOT ENDPOINTS ====================

@app.get("/chatbot", response_class=HTMLResponse)
async def chatbot_page(request: Request, user: dict = Depends(require_auth)):
    """Render chatbot page"""
    return render_page("chat.html", {"request": request, "user": user, "personas": whatsapp_bot.CHATBOT_PERSONAS})


@app.post("/api/chatbot/send")
async def chatbot_send(data: dict, user: dict = Depends(require_auth)):
    """Send a message to the chatbot and get a response"""
    message = data.get("message", "").strip()
    persona = data.get("persona", "chat")

    if not message:
        return {"status": "error", "message": "Message cannot be empty"}

    if len(message) > 2000:
        return {"status": "error", "message": "Message too long (max 2000 characters)"}

    if persona not in whatsapp_bot.CHATBOT_PERSONAS:
        persona = "chat"

    # Save user message
    database.save_chat_message(user["id"], "user", message, persona)

    # Get conversation context (last 20 messages)
    context = database.get_chat_context(user["id"], limit=20, persona=persona)

    # Run sync HTTP call in thread pool to avoid blocking the event loop
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(
            pool, lambda: whatsapp_bot.generate_chatbot_response(message, context, persona)
        )

    if result.get("success"):
        response_text = result["response"]
        # Save assistant response
        database.save_chat_message(user["id"], "assistant", response_text, persona)
        return {"status": "success", "response": response_text}
    else:
        return {"status": "error", "message": result.get("error", "Failed to generate response")}


@app.get("/api/chatbot/history")
async def chatbot_history(persona: str = "chat", user: dict = Depends(require_auth)):
    """Get chat history for the current user"""
    if persona not in whatsapp_bot.CHATBOT_PERSONAS:
        persona = "chat"

    messages = database.get_chat_history(user["id"], limit=50, persona=persona)
    return {"status": "success", "messages": messages}


@app.post("/api/chatbot/clear")
async def chatbot_clear(data: dict, user: dict = Depends(require_auth)):
    """Clear chat history"""
    persona = data.get("persona", "tutor")
    database.clear_chat_history(user["id"], persona)
    return {"status": "success", "message": "Chat history cleared"}


# ==================== SCHEDULED TASKS ====================

def send_daily_vocabulary():
    """Send daily vocabulary to all active subscribers"""
    # Get current hour in HH:MM format
    current_time = datetime.now().strftime("%H:%M")
    
    print(f"[{datetime.now()}] Checking for users with preferred time: {current_time}")
    
    # Get users who want messages at this time
    users = database.get_users_by_time(current_time)
    
    if users:
        print(f"Found {len(users)} users wanting words at {current_time}")
        result = whatsapp_bot.send_to_all_subscribers(users)
        print(f"Daily vocab sent: {result}")
    else:
        print(f"No users scheduled for {current_time}")

# ==================== MAIN ====================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)