"""
VocabPro - Database Module
PostgreSQL for production, SQLite for local
"""

import os
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict

# Check if PostgreSQL is configured
USE_POSTGRES = os.environ.get("DB_HOST") is not None

if USE_POSTGRES:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    DB_HOST = os.environ.get("DB_HOST")
    DB_PORT = os.environ.get("DB_PORT", "5432")
    DB_NAME = os.environ.get("DB_NAME", "db")
    DB_USER = os.environ.get("DB_USER", "pgres")
    DB_PASSWORD = os.environ.get("DB_PASSWORD")
else:
    import sqlite3
    SQLITE_DB = "vocabpro.db"

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hashlib.sha256(password.encode()).hexdigest() == hashed

def _row_to_dict(cursor, row):
    """Convert a database row to a dict using cursor description"""
    if not row:
        return None
    columns = [desc[0] for desc in cursor.description] if cursor.description else []
    return dict(zip(columns, row)) if columns else None

def _rows_to_dicts(cursor, rows):
    """Convert multiple database rows to dicts"""
    if not rows:
        return []
    columns = [desc[0] for desc in cursor.description] if cursor.description else []
    return [dict(zip(columns, row)) for row in rows] if columns else []

def get_db_connection():
    """Get database connection"""
    if USE_POSTGRES:
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            return conn
        except Exception as e:
            print(f"PostgreSQL connection error: {e}")
            return None
    else:
        try:
            conn = sqlite3.connect(SQLITE_DB)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            print(f"SQLite connection error: {e}")
            return None

def init_db():
    """Initialize database with tables"""
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database")
        return
    
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            whatsapp_number TEXT NOT NULL,
            is_subscribed BOOLEAN DEFAULT FALSE,
            trial_ends DATE,
            is_paid BOOLEAN DEFAULT FALSE,
            paid_date DATE,
            is_admin BOOLEAN DEFAULT FALSE,
            timezone TEXT DEFAULT 'Asia/Dhaka',
            preferred_time TEXT DEFAULT '09:30',
            preferred_category TEXT DEFAULT 'ielts',
            last_word_index INTEGER DEFAULT 0,
            words_learned INTEGER DEFAULT 0,
            referral_code TEXT UNIQUE,
            referred_by INTEGER,
            referral_count INTEGER DEFAULT 0,
            free_months_earned INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            transaction_id TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            verified_by TEXT,
            verified_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vocabulary (
            id SERIAL PRIMARY KEY,
            word TEXT NOT NULL,
            phonetic TEXT,
            meaning_bn TEXT NOT NULL,
            example TEXT,
            category TEXT DEFAULT 'general'
        )
    """)
    
    conn.commit()

    # Migration: add preferred_category column if missing
    try:
        if USE_POSTGRES:
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS preferred_category TEXT DEFAULT 'ielts'")
        else:
            cursor.execute("PRAGMA table_info(users)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'preferred_category' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN preferred_category TEXT DEFAULT 'ielts'")
        conn.commit()
    except Exception as e:
        print(f"Migration note: {e}")

    # Migration: add reset code columns if missing
    try:
        if USE_POSTGRES:
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_code TEXT")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_code_expires TIMESTAMP")
        else:
            cursor.execute("PRAGMA table_info(users)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'reset_code' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN reset_code TEXT")
            if 'reset_code_expires' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN reset_code_expires TIMESTAMP")
        conn.commit()
    except Exception as e:
        print(f"Migration note: {e}")

    # Migration: add leaderboard fields if missing
    try:
        if USE_POSTGRES:
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS weekly_words_learned INTEGER DEFAULT 0")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS monthly_words_learned INTEGER DEFAULT 0")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS week_start_date DATE")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS month_start_date DATE")
        else:
            cursor.execute("PRAGMA table_info(users)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'weekly_words_learned' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN weekly_words_learned INTEGER DEFAULT 0")
            if 'monthly_words_learned' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN monthly_words_learned INTEGER DEFAULT 0")
            if 'week_start_date' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN week_start_date DATE")
            if 'month_start_date' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN month_start_date DATE")
        conn.commit()
    except Exception as e:
        print(f"Migration note: {e}")

    # Chat messages table
    try:
        if USE_POSTGRES:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    persona TEXT DEFAULT 'tutor',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_user_time ON chat_messages(user_id, created_at)")
        else:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    persona TEXT DEFAULT 'tutor',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_user_time ON chat_messages(user_id, created_at)")
        # Fix: ensure users id column is SERIAL with working sequence
        if USE_POSTGRES:
            try:
                # Check if sequence exists for users.id
                cursor.execute("SELECT pg_get_serial_sequence('users', 'id')")
                seq = cursor.fetchone()
                if not seq or not seq[0]:
                    print("No sequence for users.id, adding one...")
                    cursor.execute("CREATE SEQUENCE IF NOT EXISTS users_id_seq OWNED BY users.id")
                    cursor.execute("ALTER TABLE users ALTER COLUMN id SET DEFAULT nextval('users_id_seq')")
                    cursor.execute("SELECT setval('users_id_seq', COALESCE((SELECT MAX(id) FROM users), 0))")
                    conn.commit()
                    print("Fixed users.id sequence")

                # Fix any null ids
                cursor.execute("UPDATE users SET id = nextval('users_id_seq') WHERE id IS NULL")
                conn.commit()
            except Exception as fix_err:
                print(f"ID fix note: {fix_err}")
                conn.rollback()
        conn.commit()
    except Exception as e:
        print(f"Migration note: {e}")

    cursor.close()
    conn.close()
    print("Database initialized successfully!")

import secrets
import string

def generate_referral_code() -> str:
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))

def create_user(name: str, email: str, phone: str, password: str, whatsapp: str, referred_by: int = None, preferred_category: str = "ielts") -> Optional[int]:
    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor()

    try:
        password_hash = hash_password(password)
        trial_end = (datetime.now() + timedelta(days=7)).date().isoformat()
        referral_code = generate_referral_code()

        if USE_POSTGRES:
            cursor.execute("""
                INSERT INTO users (name, email, phone, password_hash, whatsapp_number, trial_ends, is_subscribed, referral_code, referred_by, preferred_category)
                VALUES (%s, %s, %s, %s, %s, %s, TRUE, %s, %s, %s)
                RETURNING id
            """, (name, email, phone, password_hash, whatsapp, trial_end, referral_code, referred_by, preferred_category))
            user_id = cursor.fetchone()[0]
        else:
            cursor.execute("""
                INSERT INTO users (name, email, phone, password_hash, whatsapp_number, trial_ends, is_subscribed, referral_code, referred_by, preferred_category)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
            """, (name, email, phone, password_hash, whatsapp, trial_end, referral_code, referred_by, preferred_category))
            user_id = cursor.lastrowid
        
        if referred_by:
            if USE_POSTGRES:
                cursor.execute("UPDATE users SET referral_count = referral_count + 1 WHERE id = %s", (referred_by,))
            else:
                cursor.execute("UPDATE users SET referral_count = referral_count + 1 WHERE id = ?", (referred_by,))
        
        conn.commit()
        cursor.close()
        conn.close()
        return user_id
    except Exception:
        conn.close()
        return None

def verify_user(email: str, password: str) -> Optional[dict]:
    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor()

    if USE_POSTGRES:
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    else:
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))

    columns = [desc[0] for desc in cursor.description] if cursor.description else []
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    user = dict(zip(columns, row)) if columns else None
    if user and verify_password(password, user.get("password_hash", "")):
        return user
    return None

def get_user_by_id(user_id: int) -> Optional[dict]:
    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor()

    if USE_POSTGRES:
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    else:
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))

    columns = [desc[0] for desc in cursor.description] if cursor.description else []
    row = cursor.fetchone()
    conn.close()

    return dict(zip(columns, row)) if row and columns else None

def update_user_profile(user_id: int, data: dict) -> bool:
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    try:
        if USE_POSTGRES:
            cursor.execute("""
                UPDATE users SET 
                    name = %s, phone = %s, whatsapp_number = %s, 
                    preferred_time = %s, timezone = %s
                WHERE id = %s
            """, (data.get("name"), data.get("phone"), data.get("whatsapp_number"),
                  data.get("preferred_time"), data.get("timezone"), user_id))
        else:
            cursor.execute("""
                UPDATE users SET 
                    name = ?, phone = ?, whatsapp_number = ?, 
                    preferred_time = ?, timezone = ?
                WHERE id = ?
            """, (data.get("name"), data.get("phone"), data.get("whatsapp_number"),
                  data.get("preferred_time"), data.get("timezone"), user_id))
        
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error updating profile: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def update_password(user_id: int, new_hash: str) -> bool:
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    try:
        if USE_POSTGRES:
            cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (new_hash, user_id))
        else:
            cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
        
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error updating password: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def get_user_by_email(email: str) -> Optional[dict]:
    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor()

    if USE_POSTGRES:
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    else:
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))

    user = cursor.fetchone()
    result = _row_to_dict(cursor, user)
    cursor.close()
    conn.close()

    return result

def get_all_users() -> list:
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
    users = cursor.fetchall()
    conn.close()
    
    if not users:
        return []
    
    result = []
    for u in users:
        try:
            if hasattr(u, '_asdict'):
                result.append(u._asdict())
            else:
                result.append(dict(u))
        except Exception:
            try:
                result.append({k: u[i] for i, k in enumerate(u.keys())})
            except Exception:
                pass
    return result

def get_active_subscribers() -> list:
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor()
    
    if USE_POSTGRES:
        cursor.execute("SELECT * FROM users WHERE is_paid = TRUE")
    else:
        cursor.execute("SELECT * FROM users WHERE is_paid = 1")
    
    users = cursor.fetchall()
    conn.close()
    
    if not users:
        return []
    if hasattr(users[0], '_asdict'):
        return [u._asdict() for u in users]
    return _rows_to_dicts(cursor, users)

def get_all_subscribers() -> list:
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor()
    
    if USE_POSTGRES:
        cursor.execute("SELECT * FROM users WHERE is_subscribed = TRUE")
    else:
        cursor.execute("SELECT * FROM users WHERE is_subscribed = 1")
    
    users = cursor.fetchall()
    conn.close()

    if not users:
        return []
    if hasattr(users[0], '_asdict'):
        return [u._asdict() for u in users]
    return _rows_to_dicts(cursor, users)

def get_users_by_time(time: str) -> list:
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor()
    
    if USE_POSTGRES:
        cursor.execute("SELECT * FROM users WHERE preferred_time = %s AND is_subscribed = TRUE", (time,))
    else:
        cursor.execute("SELECT * FROM users WHERE preferred_time = ? AND is_subscribed = 1", (time,))
    
    users = cursor.fetchall()
    conn.close()
    
    if not users:
        return []
    if hasattr(users[0], '_asdict'):
        return [u._asdict() for u in users]
    return _rows_to_dicts(cursor, users)

def update_preferred_time(user_id: int, preferred_time: str) -> bool:
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    if USE_POSTGRES:
        cursor.execute("UPDATE users SET preferred_time = %s WHERE id = %s", (preferred_time, user_id))
    else:
        cursor.execute("UPDATE users SET preferred_time = ? WHERE id = ?", (preferred_time, user_id))
    
    conn.commit()
    success = cursor.rowcount > 0
    cursor.close()
    conn.close()
    return success

def update_preferred_category(user_id: int, preferred_category: str) -> bool:
    """Update user's preferred word category (called by admin only)"""
    conn = get_db_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    if USE_POSTGRES:
        cursor.execute("UPDATE users SET preferred_category = %s WHERE id = %s", (preferred_category, user_id))
    else:
        cursor.execute("UPDATE users SET preferred_category = ? WHERE id = ?", (preferred_category, user_id))
    conn.commit()
    success = cursor.rowcount > 0
    cursor.close()
    conn.close()
    return success

def create_category_request(user_id: int, requested_category: str) -> dict:
    """Submit a category change request. Max 2 per calendar month."""
    from datetime import datetime, timedelta
    conn = get_db_connection()
    if not conn:
        return {"success": False, "message": "Database error"}
    cursor = conn.cursor()

    # Check how many requests this month
    now = datetime.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_start_str = month_start.strftime("%Y-%m-%d %H:%M:%S")

    if USE_POSTGRES:
        cursor.execute("SELECT COUNT(*) FROM category_requests WHERE user_id = %s AND created_at >= %s",
                       (user_id, month_start_str))
    else:
        cursor.execute("SELECT COUNT(*) FROM category_requests WHERE user_id = ? AND created_at >= ?",
                       (user_id, month_start_str))

    count = cursor.fetchone()[0]
    if count >= 2:
        cursor.close()
        conn.close()
        return {"success": False, "message": "You can send maximum 2 category change requests per month."}

    # Check for pending request
    if USE_POSTGRES:
        cursor.execute("SELECT COUNT(*) FROM category_requests WHERE user_id = %s AND status = 'pending'", (user_id,))
    else:
        cursor.execute("SELECT COUNT(*) FROM category_requests WHERE user_id = ? AND status = 'pending'", (user_id,))

    pending = cursor.fetchone()[0]
    if pending > 0:
        cursor.close()
        conn.close()
        return {"success": False, "message": "You already have a pending request. Wait for admin approval."}

    # Create request
    if USE_POSTGRES:
        cursor.execute("INSERT INTO category_requests (user_id, requested_category) VALUES (%s, %s)",
                       (user_id, requested_category))
    else:
        cursor.execute("INSERT INTO category_requests (user_id, requested_category) VALUES (?, ?)",
                       (user_id, requested_category))

    conn.commit()
    cursor.close()
    conn.close()
    return {"success": True, "message": "Request submitted. Admin will review it soon."}

def get_pending_category_requests() -> list:
    """Get all pending category change requests"""
    conn = get_db_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cr.id, cr.user_id, u.name, u.email, cr.requested_category, cr.created_at
        FROM category_requests cr
        JOIN users u ON cr.user_id = u.id
        WHERE cr.status = 'pending'
        ORDER BY cr.created_at DESC
    """)
    rows = cursor.fetchall()
    requests = []
    for r in rows:
        requests.append({
            "id": r[0], "user_id": r[1], "user_name": r[2], "user_email": r[3],
            "requested_category": r[4], "created_at": r[5]
        })
    cursor.close()
    conn.close()
    return requests

def approve_category_request(request_id: int, admin_user: str) -> bool:
    """Approve a category change request"""
    from datetime import datetime
    conn = get_db_connection()
    if not conn:
        return False
    cursor = conn.cursor()

    # Get request
    if USE_POSTGRES:
        cursor.execute("SELECT user_id, requested_category FROM category_requests WHERE id = %s AND status = 'pending'", (request_id,))
    else:
        cursor.execute("SELECT user_id, requested_category FROM category_requests WHERE id = ? AND status = 'pending'", (request_id,))

    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        return False

    user_id, requested_category = row
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Update request status
    if USE_POSTGRES:
        cursor.execute("UPDATE category_requests SET status = 'approved', resolved_at = %s, resolved_by = %s WHERE id = %s",
                       (now, admin_user, request_id))
    else:
        cursor.execute("UPDATE category_requests SET status = 'approved', resolved_at = ?, resolved_by = ? WHERE id = ?",
                       (now, admin_user, request_id))

    # Update user's category
    if USE_POSTGRES:
        cursor.execute("UPDATE users SET preferred_category = %s WHERE id = %s", (requested_category, user_id))
    else:
        cursor.execute("UPDATE users SET preferred_category = ? WHERE id = ?", (requested_category, user_id))

    conn.commit()
    cursor.close()
    conn.close()
    return True

def reject_category_request(request_id: int, admin_user: str) -> bool:
    """Reject a category change request"""
    from datetime import datetime
    conn = get_db_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if USE_POSTGRES:
        cursor.execute("UPDATE category_requests SET status = 'rejected', resolved_at = %s, resolved_by = %s WHERE id = %s",
                       (now, admin_user, request_id))
    else:
        cursor.execute("UPDATE category_requests SET status = 'rejected', resolved_at = ?, resolved_by = ? WHERE id = ?",
                       (now, admin_user, request_id))
    conn.commit()
    success = cursor.rowcount > 0
    cursor.close()
    conn.close()
    return success
    return success

def store_reset_code(whatsapp_number: str, code: str, expires_at: str) -> bool:
    """Store a password reset code for a user"""
    conn = get_db_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        if USE_POSTGRES:
            cursor.execute("UPDATE users SET reset_code = %s, reset_code_expires = %s WHERE whatsapp_number = %s",
                           (code, expires_at, whatsapp_number))
        else:
            cursor.execute("UPDATE users SET reset_code = ?, reset_code_expires = ? WHERE whatsapp_number = ?",
                           (code, expires_at, whatsapp_number))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error storing reset code: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def verify_reset_code(whatsapp_number: str, code: str) -> bool:
    """Verify a reset code is valid and not expired"""
    conn = get_db_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if USE_POSTGRES:
            cursor.execute("""
                SELECT id FROM users
                WHERE whatsapp_number = %s AND reset_code = %s AND reset_code_expires > %s
            """, (whatsapp_number, code, now))
        else:
            cursor.execute("""
                SELECT id FROM users
                WHERE whatsapp_number = ? AND reset_code = ? AND reset_code_expires > ?
            """, (whatsapp_number, code, now))
        return cursor.fetchone() is not None
    except Exception as e:
        print(f"Error verifying reset code: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def clear_reset_code(whatsapp_number: str) -> bool:
    """Clear reset code after successful password reset"""
    conn = get_db_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        if USE_POSTGRES:
            cursor.execute("UPDATE users SET reset_code = NULL, reset_code_expires = NULL WHERE whatsapp_number = %s",
                           (whatsapp_number,))
        else:
            cursor.execute("UPDATE users SET reset_code = NULL, reset_code_expires = NULL WHERE whatsapp_number = ?",
                           (whatsapp_number,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error clearing reset code: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def update_last_word_index(user_id: int, word_index: int) -> bool:
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    if USE_POSTGRES:
        cursor.execute("UPDATE users SET last_word_index = %s WHERE id = %s", (word_index, user_id))
    else:
        cursor.execute("UPDATE users SET last_word_index = ? WHERE id = ?", (word_index, user_id))
    
    conn.commit()
    success = cursor.rowcount > 0
    cursor.close()
    conn.close()
    return success

def update_user_subscription(user_id: int, is_paid: bool = True):
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    if is_paid:
        if USE_POSTGRES:
            cursor.execute("""
                UPDATE users 
                SET is_paid = TRUE, paid_date = %s, is_subscribed = TRUE
                WHERE id = %s
            """, (datetime.now().date().isoformat(), user_id))
        else:
            cursor.execute("""
                UPDATE users 
                SET is_paid = 1, paid_date = ?, is_subscribed = 1
                WHERE id = ?
            """, (datetime.now().date().isoformat(), user_id))
    else:
        if USE_POSTGRES:
            cursor.execute("UPDATE users SET is_paid = FALSE, is_subscribed = FALSE WHERE id = %s", (user_id,))
        else:
            cursor.execute("UPDATE users SET is_paid = 0, is_subscribed = 0 WHERE id = ?", (user_id,))
    
    conn.commit()
    cursor.close()
    conn.close()

def delete_user(user_id: int):
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    if USE_POSTGRES:
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    else:
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    
    conn.commit()
    cursor.close()
    conn.close()

def create_payment(user_id: int, amount: int, transaction_id: str) -> Optional[int]:
    conn = get_db_connection()
    if not conn:
        return None
    
    cursor = conn.cursor()
    
    if USE_POSTGRES:
        cursor.execute("""
            INSERT INTO payments (user_id, amount, transaction_id, status)
            VALUES (%s, %s, %s, 'pending')
            RETURNING id
        """, (user_id, amount, transaction_id))
        payment_id = cursor.fetchone()[0]
    else:
        cursor.execute("""
            INSERT INTO payments (user_id, amount, transaction_id, status)
            VALUES (?, ?, ?, 'pending')
        """, (user_id, amount, transaction_id))
        payment_id = cursor.lastrowid
    
    conn.commit()
    cursor.close()
    conn.close()
    return payment_id

def get_pending_payments() -> list:
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor()
    
    if USE_POSTGRES:
        cursor.execute("""
            SELECT p.*, u.name, u.email, u.whatsapp_number
            FROM payments p
            JOIN users u ON p.user_id = u.id
            WHERE p.status = 'pending'
            ORDER BY p.created_at DESC
        """)
    else:
        cursor.execute("""
            SELECT p.*, u.name, u.email, u.whatsapp_number
            FROM payments p
            JOIN users u ON p.user_id = u.id
            WHERE p.status = 'pending'
            ORDER BY p.created_at DESC
        """)
    
    payments = cursor.fetchall()
    conn.close()
    
    if not payments:
        return []
    if hasattr(payments[0], '_asdict'):
        return [p._asdict() for p in payments]
    return _rows_to_dicts(cursor, payments)

def approve_payment(payment_id: int, admin_username: str):
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    if USE_POSTGRES:
        cursor.execute("SELECT user_id FROM payments WHERE id = %s", (payment_id,))
    else:
        cursor.execute("SELECT user_id FROM payments WHERE id = ?", (payment_id,))
    
    payment = cursor.fetchone()
    
    if payment:
        user_id = payment[0]
        
        if USE_POSTGRES:
            cursor.execute("""
                UPDATE payments 
                SET status = 'approved', verified_by = %s, verified_at = %s
                WHERE id = %s
            """, (admin_username, datetime.now().isoformat(), payment_id))
            
            cursor.execute("""
                UPDATE users 
                SET is_paid = TRUE, paid_date = %s, is_subscribed = TRUE
                WHERE id = %s
            """, (datetime.now().date().isoformat(), user_id))
        else:
            cursor.execute("""
                UPDATE payments 
                SET status = 'approved', verified_by = ?, verified_at = ?
                WHERE id = ?
            """, (admin_username, datetime.now().isoformat(), payment_id))
            
            cursor.execute("""
                UPDATE users 
                SET is_paid = 1, paid_date = ?, is_subscribed = 1
                WHERE id = ?
            """, (datetime.now().date().isoformat(), user_id))
    
    conn.commit()
    cursor.close()
    conn.close()

def reject_payment(payment_id: int):
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    if USE_POSTGRES:
        cursor.execute("UPDATE payments SET status = 'rejected' WHERE id = %s", (payment_id,))
    else:
        cursor.execute("UPDATE payments SET status = 'rejected' WHERE id = ?", (payment_id,))
    
    conn.commit()
    cursor.close()
    conn.close()

def get_user_payments(user_id: int) -> list:
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor()
    
    if USE_POSTGRES:
        cursor.execute("SELECT * FROM payments WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
    else:
        cursor.execute("SELECT * FROM payments WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    
    payments = cursor.fetchall()
    conn.close()
    
    if not payments:
        return []
    if hasattr(payments[0], '_asdict'):
        return [p._asdict() for p in payments]
    return _rows_to_dicts(cursor, payments)

def get_stats() -> dict:
    conn = get_db_connection()
    if not conn:
        return {"total_users": 0, "active_subscribers": 0, "trial_users": 0, "pending_payments": 0, "monthly_revenue": 0, "total_revenue": 0}
    
    cursor = conn.cursor()
    
    if USE_POSTGRES:
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_paid = TRUE")
        active_subscribers = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_paid = FALSE AND trial_ends >= %s", (datetime.now().date().isoformat(),))
        trial_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM payments WHERE status = 'pending'")
        pending_payments = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM payments 
            WHERE status = 'approved' AND verified_at >= date_trunc('month', CURRENT_DATE)
        """)
        monthly_revenue = cursor.fetchone()[0]
        
        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'approved'")
        total_revenue = cursor.fetchone()[0]
    else:
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_paid = 1")
        active_subscribers = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_paid = 0 AND trial_ends >= ?", (datetime.now().date().isoformat(),))
        trial_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM payments WHERE status = 'pending'")
        pending_payments = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM payments 
            WHERE status = 'approved' AND verified_at >= date('now', 'start of month')
        """)
        monthly_revenue = cursor.fetchone()[0]
        
        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'approved'")
        total_revenue = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "total_users": total_users,
        "active_subscribers": active_subscribers,
        "trial_users": trial_users,
        "pending_payments": pending_payments,
        "monthly_revenue": monthly_revenue,
        "total_revenue": total_revenue
    }

def get_user_stats(user_id: int) -> dict:
    conn = get_db_connection()
    if not conn:
        return {}

    cursor = conn.cursor()

    if USE_POSTGRES:
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    else:
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))

    columns = [desc[0] for desc in cursor.description] if cursor.description else []
    row = cursor.fetchone()

    if not row:
        conn.close()
        return {}

    user = dict(zip(columns, row)) if columns else {}

    if USE_POSTGRES:
        cursor.execute("SELECT COUNT(*) FROM users WHERE words_learned > %s", (user.get("words_learned", 0),))
    else:
        cursor.execute("SELECT COUNT(*) FROM users WHERE words_learned > ?", (user.get("words_learned", 0),))

    users_ahead = cursor.fetchone()[0]

    if USE_POSTGRES:
        cursor.execute("SELECT COUNT(*) FROM users")
    else:
        cursor.execute("SELECT COUNT(*) FROM users")

    total = cursor.fetchone()[0]

    percentile = 100 - (users_ahead / total * 100) if total > 0 else 0

    conn.close()

    return {
        "words_learned": user.get("words_learned", 0),
        "word_index": user.get("last_word_index", 0),
        "referral_count": user.get("referral_count", 0),
        "free_months": user.get("free_months_earned", 0),
        "percentile": round(percentile, 1),
        "subscription": "Pro" if user.get("is_paid") else "Trial"
    }

def get_daily_vocabulary(count: int = 10) -> list:
    conn = get_db_connection()
    if not conn:
        return get_default_vocabulary()
    
    cursor = conn.cursor()
    
    if USE_POSTGRES:
        cursor.execute("SELECT * FROM vocabulary ORDER BY RANDOM() LIMIT %s", (count,))
    else:
        cursor.execute("SELECT * FROM vocabulary ORDER BY RANDOM() LIMIT ?", (count,))
    
    words = cursor.fetchall()
    conn.close()
    
    if not words:
        return get_default_vocabulary()
    if hasattr(words[0], '_asdict'):
        return [w._asdict() for w in words]
    return _rows_to_dicts(cursor, words)

def get_default_vocabulary() -> list:
    return [
        {"word": "Ubiquitous", "meaning_bn": "সর্বত্র বিদ্যমান", "example": "Smartphones are ubiquitous in modern society."},
        {"word": "Pragmatic", "meaning_bn": "বাস্তবসম্মত", "example": "She took a pragmatic approach to solving the problem."},
        {"word": "Eloquent", "meaning_bn": "বাকপটু", "example": "His eloquent speech moved the audience."},
        {"word": "Benevolent", "meaning_bn": "দয়ালু", "example": "The benevolent donor gave millions to charity."},
        {"word": "Ambiguous", "meaning_bn": "অস্পষ্ট", "example": "The contract contains several ambiguous clauses."},
    ]

def get_vocabulary_words(count: int = 10, start_index: int = 0, category: str = None) -> list:
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor()

    if category and category != "all":
        cat_pattern = f"%{category}%"
        if USE_POSTGRES:
            cursor.execute("SELECT * FROM vocabulary WHERE LOWER(category) LIKE LOWER(%s) ORDER BY id LIMIT %s OFFSET %s", (cat_pattern, count, start_index))
        else:
            cursor.execute("SELECT * FROM vocabulary WHERE LOWER(category) LIKE LOWER(?) ORDER BY id LIMIT ? OFFSET ?", (cat_pattern, count, start_index))
    else:
        if USE_POSTGRES:
            cursor.execute("SELECT * FROM vocabulary ORDER BY id LIMIT %s OFFSET %s", (count, start_index))
        else:
            cursor.execute("SELECT * FROM vocabulary ORDER BY id LIMIT ? OFFSET ?", (count, start_index))

    words = cursor.fetchall()
    conn.close()
    
    if not words:
        return []
    
    result = []
    for w in words:
        word_data = dict(w)
        word_data["meaning"] = word_data.get("meaning_bn", "")
        result.append(word_data)
    
    return result

def get_vocabulary_count() -> int:
    conn = get_db_connection()
    if not conn:
        return 0
    
    cursor = conn.cursor()
    
    if USE_POSTGRES:
        cursor.execute("SELECT COUNT(*) FROM vocabulary")
    else:
        cursor.execute("SELECT COUNT(*) FROM vocabulary")
    
    count = cursor.fetchone()[0]
    conn.close()
    
    return count

def clear_all_vocabulary() -> bool:
    """Delete all vocabulary words from the database"""
    conn = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM vocabulary")
        conn.commit()
        return True
    except Exception as e:
        print(f"Error clearing vocabulary: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def get_all_vocabulary() -> list:
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor()
    cursor.execute("SELECT id, word, phonetic, meaning_bn, example, category FROM vocabulary ORDER BY id DESC")
    words = cursor.fetchall()
    conn.close()
    
    if not words:
        return []
    
    result = []
    for w in words:
        try:
            if hasattr(w, '_asdict'):
                result.append(w._asdict())
            else:
                result.append(dict(w))
        except Exception:
            result.append({'id': w[0], 'word': w[1], 'phonetic': w[2], 'meaning_bn': w[3], 'example': w[4]})
    return result

def get_existing_words(word_list: list) -> set:
    """Check which words already exist in database (case-insensitive). Returns set of lowercase words."""
    conn = get_db_connection()
    if not conn:
        return set()

    cursor = conn.cursor()
    try:
        # Get all existing words
        cursor.execute("SELECT LOWER(word) FROM vocabulary")
        existing = set(row[0] for row in cursor.fetchall())

        # Return intersection with the input list
        return set(w.lower() for w in word_list if w.lower() in existing)
    except Exception as e:
        print(f"Error checking existing words: {e}")
        return set()
    finally:
        cursor.close()
        conn.close()

def add_vocabulary_word(word: str, meaning_bn: str, example: str = "", category: str = "", phonetic: str = "") -> bool:
    conn = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        if USE_POSTGRES:
            cursor.execute("""
                INSERT INTO vocabulary (word, phonetic, meaning_bn, example, category)
                VALUES (%s, %s, %s, %s, %s)
            """, (word, phonetic, meaning_bn, example, category))
        else:
            cursor.execute("""
                INSERT INTO vocabulary (word, phonetic, meaning_bn, example, category)
                VALUES (?, ?, ?, ?, ?)
            """, (word, phonetic, meaning_bn, example, category))

        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding vocabulary: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def bulk_insert_vocabulary(words: list) -> dict:
    """Insert multiple vocabulary words in a single transaction. Much faster than individual inserts."""
    conn = get_db_connection()
    if not conn:
        return {"success": 0, "failed": len(words)}

    cursor = conn.cursor()
    success_count = 0
    failed_count = 0

    try:
        for w in words:
            word = w.get("word", "").strip()
            if not word:
                failed_count += 1
                continue

            phonetic = w.get("phonetic", "")
            meaning_bn = w.get("meaning_bn", "")
            example = w.get("example", "")
            category = w.get("category", "general")

            try:
                if USE_POSTGRES:
                    cursor.execute("""
                        INSERT INTO vocabulary (word, phonetic, meaning_bn, example, category)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (word, phonetic, meaning_bn, example, category))
                else:
                    cursor.execute("""
                        INSERT INTO vocabulary (word, phonetic, meaning_bn, example, category)
                        VALUES (?, ?, ?, ?, ?)
                    """, (word, phonetic, meaning_bn, example, category))
                success_count += 1
            except Exception:
                failed_count += 1

        conn.commit()
    except Exception as e:
        print(f"Bulk insert error: {e}")
        conn.rollback()
        failed_count = len(words) - success_count
    finally:
        cursor.close()
        conn.close()

    return {"success": success_count, "failed": failed_count}

def seed_vocabulary():
    words = [
        ("Ubiquitous", "সর্বত্র বিদ্যমান", "Smartphones are ubiquitous in modern society.", "IELTS"),
        ("Pragmatic", "বাস্তবসম্মত", "She took a pragmatic approach to solving the problem.", "IELTS"),
        ("Eloquent", "বাকপটু", "His eloquent speech moved the audience.", "IELTS"),
        ("Benevolent", "দয়ালু", "The benevolent donor gave millions to charity.", "GRE"),
        ("Ambiguous", "অস্পষ্ট", "The contract contains several ambiguous clauses.", "IELTS"),
    ]
    
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    for word, meaning, example, category in words:
        try:
            if USE_POSTGRES:
                cursor.execute("""
                    INSERT INTO vocabulary (word, meaning_bn, example, category)
                    VALUES (%s, %s, %s, %s)
                """, (word, meaning, example, category))
            else:
                cursor.execute("""
                    INSERT OR IGNORE INTO vocabulary (word, meaning_bn, example, category)
                    VALUES (?, ?, ?, ?)
                """, (word, meaning, example, category))
        except:
            pass
    
    conn.commit()
    cursor.close()
    conn.close()

# ==================== PROGRESS TRACKING ====================

def get_user_progress(user_id: int) -> dict:
    """Get user's progress data"""
    conn = get_db_connection()
    if not conn:
        return {"streak": 0, "total_words": 0, "this_week": 0, "this_month": 0}
    
    cursor = conn.cursor()
    
    try:
        if USE_POSTGRES:
            cursor.execute("""
                SELECT streak_days, words_learned, total_words_sent, last_active_date 
                FROM users WHERE id = %s
            """, (user_id,))
        else:
            cursor.execute("""
                SELECT streak_days, words_learned, total_words_sent, last_active_date 
                FROM users WHERE id = ?
            """, (user_id,))
        
        row = cursor.fetchone()
        
        if row:
            return {
                "streak": row[0] or 0,
                "total_words": row[1] or 0,
                "words_sent": row[2] or 0,
                "last_active": str(row[3]) if row[3] else None
            }
    except Exception as e:
        print(f"Error getting progress: {e}")
    
    cursor.close()
    conn.close()
    return {"streak": 0, "total_words": 0, "words_sent": 0, "last_active": None}

def update_user_progress(user_id: int) -> bool:
    """Update user's streak and activity"""
    from datetime import datetime, timedelta
    
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    today = datetime.now().date()
    
    try:
        # Get current streak and last active date
        if USE_POSTGRES:
            cursor.execute("SELECT streak_days, last_active_date FROM users WHERE id = %s", (user_id,))
        else:
            cursor.execute("SELECT streak_days, last_active_date FROM users WHERE id = ?", (user_id,))
        
        row = cursor.fetchone()
        current_streak = row[0] if row else 0
        last_active = row[1] if row and row[1] else None
        
        # Calculate new streak
        if last_active:
            last_date = last_active
            if isinstance(last_active, str):
                last_date = datetime.strptime(last_active, "%Y-%m-%d").date()
            
            days_diff = (today - last_date).days
            
            if days_diff == 0:
                # Already active today, no change
                new_streak = current_streak
            elif days_diff == 1:
                # Consecutive day, increment streak
                new_streak = current_streak + 1
            else:
                # Streak broken, reset to 1
                new_streak = 1
        else:
            # First time active
            new_streak = 1
        
        # Update
        if USE_POSTGRES:
            cursor.execute("""
                UPDATE users SET streak_days = %s, last_active_date = %s 
                WHERE id = %s
            """, (new_streak, today, user_id))
        else:
            cursor.execute("""
                UPDATE users SET streak_days = ?, last_active_date = ? 
                WHERE id = ?
            """, (new_streak, today, user_id))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating progress: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

# ==================== ACHIEVEMENTS ====================

ACHIEVEMENTS = [
    {"id": "first_word", "name": "🎯 First Word", "desc": "Start your vocabulary journey", "icon": "🎯", "condition": "words >= 1"},
    {"id": "word_10", "name": "📖 Word Explorer", "desc": "Learn 10 words", "icon": "📖", "condition": "words >= 10"},
    {"id": "word_50", "name": "📚 Word Collector", "desc": "Learn 50 words", "icon": "📚", "condition": "words >= 50"},
    {"id": "word_100", "name": "🌟 Vocabulary Master", "desc": "Learn 100 words", "icon": "🌟", "condition": "words >= 100"},
    {"id": "word_300", "name": "🏆 Word Champion", "desc": "Learn 300 words", "icon": "🏆", "condition": "words >= 300"},
    {"id": "streak_3", "name": "🔥 3-Day Streak", "desc": "3 days of learning", "icon": "🔥", "condition": "streak >= 3"},
    {"id": "streak_7", "name": "💪 7-Day Streak", "desc": "1 week of learning", "icon": "💪", "condition": "streak >= 7"},
    {"id": "streak_30", "name": "👑 30-Day Streak", "desc": "1 month of learning", "icon": "👑", "condition": "streak >= 30"},
    {"id": "pro_member", "name": "⭐ Pro Member", "desc": "Upgrade to paid plan", "icon": "⭐", "condition": "is_paid = true"},
    {"id": "quiz_first", "name": "🧠 Quiz Starter", "desc": "Complete first quiz", "icon": "🧠", "condition": "quiz_taken = true"},
    {"id": "quiz_perfect", "name": "🎯 Perfect Score", "desc": "Get 100% in quiz", "icon": "🎯", "condition": "quiz_score = 100"},
    {"id": "referral_1", "name": "📢 First Referral", "desc": "Refer your first friend", "icon": "📢", "condition": "referrals >= 1"},
]

def get_user_achievements(user_id: int) -> list:
    """Get user's achievements"""
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor()
    
    try:
        if USE_POSTGRES:
            cursor.execute("""
                SELECT achievements, words_learned, is_paid, streak_days, referral_count, quiz_high_score
                FROM users WHERE id = %s
            """, (user_id,))
        else:
            cursor.execute("""
                SELECT achievements, words_learned, is_paid, streak_days, referral_count, quiz_high_score
                FROM users WHERE id = ?
            """, (user_id,))
        
        row = cursor.fetchone()
        
        if not row:
            return []
        
        # Parse achievements from database
        try:
            earned = set(row[0] if row[0] else [])
        except:
            earned = set()
        
        user_data = {
            "words": row[1] or 0,
            "is_paid": row[2] or 0,
            "streak": row[3] or 0,
            "referrals": row[4] or 0,
            "quiz_score": row[5] or 0,
            "quiz_taken": (row[5] or 0) > 0
        }
        
        # Check each achievement
        result = []
        for ach in ACHIEVEMENTS:
            earned_time = None
            if ach["id"] in earned:
                earned_time = "earned"
            
            # Check condition
            condition_met = False
            if eval(ach["condition"], {"__builtins__": {}}, user_data):
                condition_met = True
            
            result.append({
                "id": ach["id"],
                "name": ach["name"],
                "desc": ach["desc"],
                "icon": ach["icon"],
                "earned": condition_met
            })
        
        return result
        
    except Exception as e:
        print(f"Error getting achievements: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def check_and_award_achievements(user_id: int) -> list:
    """Check and award new achievements"""
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor()
    
    try:
        if USE_POSTGRES:
            cursor.execute("""
                SELECT achievements, words_learned, is_paid, streak_days, referral_count, quiz_high_score
                FROM users WHERE id = %s
            """, (user_id,))
        else:
            cursor.execute("""
                SELECT achievements, words_learned, is_paid, streak_days, referral_count, quiz_high_score
                FROM users WHERE id = ?
            """, (user_id,))
        
        row = cursor.fetchone()
        
        if not row:
            return []
        
        # Get current achievements
        try:
            current = set(row[0] if row[0] else [])
        except:
            current = set()
        
        user_data = {
            "words": row[1] or 0,
            "is_paid": row[2] or 0,
            "streak": row[3] or 0,
            "referrals": row[4] or 0,
            "quiz_score": row[5] or 0,
            "quiz_taken": (row[5] or 0) > 0
        }
        
        # Check for new achievements
        new_achievements = []
        for ach in ACHIEVEMENTS:
            if ach["id"] in current:
                continue
            
            if eval(ach["condition"], {"__builtins__": {}}, user_data):
                current.add(ach["id"])
                new_achievements.append(ach)
        
        if new_achievements:
            # Save to database
            if USE_POSTGRES:
                cursor.execute("UPDATE users SET achievements = %s WHERE id = %s", 
                             (list(current), user_id))
            else:
                cursor.execute("UPDATE users SET achievements = ? WHERE id = ?", 
                             (list(current), user_id))
            conn.commit()
        
        return new_achievements

    except Exception as e:
        print(f"Error checking achievements: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

# ==================== ADMIN: USER MANAGEMENT ====================

def search_users(query: str = "", status: str = "all") -> list:
    """Search and filter users"""
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor()

    try:
        base_query = "SELECT * FROM users WHERE 1=1"
        params = []

        if query:
            if USE_POSTGRES:
                base_query += " AND (name ILIKE %s OR email ILIKE %s OR phone ILIKE %s)"
            else:
                base_query += " AND (name LIKE ? OR email LIKE ? OR phone LIKE ?)"
            q = f"%{query}%"
            params.extend([q, q, q])

        if status == "paid":
            base_query += " AND is_paid = " + ("TRUE" if USE_POSTGRES else "1")
        elif status == "trial":
            if USE_POSTGRES:
                base_query += " AND is_paid = FALSE AND trial_ends >= %s"
            else:
                base_query += " AND is_paid = 0 AND trial_ends >= ?"
            params.append(datetime.now().date().isoformat())
        elif status == "expired":
            if USE_POSTGRES:
                base_query += " AND is_paid = FALSE AND trial_ends < %s"
            else:
                base_query += " AND is_paid = 0 AND trial_ends < ?"
            params.append(datetime.now().date().isoformat())

        base_query += " ORDER BY created_at DESC"

        cursor.execute(base_query, params)
        users = cursor.fetchall()

        if not users:
            return []
        if hasattr(users[0], '_asdict'):
            return [u._asdict() for u in users]
        return _rows_to_dicts(cursor, users)
    except Exception as e:
        print(f"Error searching users: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def delete_user(user_id: int) -> bool:
    """Delete a user"""
    conn = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    try:
        if USE_POSTGRES:
            cursor.execute("DELETE FROM payments WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        else:
            cursor.execute("DELETE FROM payments WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting user: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def get_user_detail(user_id: int) -> dict:
    """Get full user detail with payment history"""
    conn = get_db_connection()
    if not conn:
        return {}

    cursor = conn.cursor()

    try:
        if USE_POSTGRES:
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        else:
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))

        user = cursor.fetchone()
        if not user:
            return {}

        user_dict = _row_to_dict(cursor, user)

        # Get payment history
        if USE_POSTGRES:
            cursor.execute("SELECT * FROM payments WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
        else:
            cursor.execute("SELECT * FROM payments WHERE user_id = ? ORDER BY created_at DESC", (user_id,))

        payments = cursor.fetchall()
        user_dict["payments"] = [dict(p) for p in payments]

        return user_dict
    except Exception as e:
        print(f"Error getting user detail: {e}")
        return {}
    finally:
        cursor.close()
        conn.close()


def bulk_toggle_subscription(user_ids: list, action: str) -> int:
    """Bulk activate or deactivate users. Returns count of updated users."""
    conn = get_db_connection()
    if not conn:
        return 0

    cursor = conn.cursor()
    count = 0

    try:
        is_paid = True if action == "activate" else False
        for uid in user_ids:
            if USE_POSTGRES:
                cursor.execute("UPDATE users SET is_paid = %s WHERE id = %s AND is_admin = FALSE", (is_paid, uid))
            else:
                cursor.execute("UPDATE users SET is_paid = ? WHERE id = ? AND is_admin = 0", (int(is_paid), uid))
            count += cursor.rowcount
        conn.commit()
        return count
    except Exception as e:
        print(f"Error bulk toggling: {e}")
        return 0
    finally:
        cursor.close()
        conn.close()


# ==================== ADMIN: PAYMENT MANAGEMENT ====================

def get_all_payments(status: str = "all") -> list:
    """Get all payments with optional status filter"""
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor()

    try:
        if USE_POSTGRES:
            query = """
                SELECT p.*, u.name, u.email, u.whatsapp_number
                FROM payments p JOIN users u ON p.user_id = u.id
            """
        else:
            query = """
                SELECT p.*, u.name, u.email, u.whatsapp_number
                FROM payments p JOIN users u ON p.user_id = u.id
            """

        if status and status != "all":
            query += " WHERE p.status = " + ("%s" if USE_POSTGRES else "?")
            cursor.execute(query + " ORDER BY p.created_at DESC", (status,))
        else:
            cursor.execute(query + " ORDER BY p.created_at DESC")

        payments = cursor.fetchall()
        return _rows_to_dicts(cursor, payments)
    except Exception as e:
        print(f"Error getting payments: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def get_revenue_stats() -> dict:
    """Get revenue breakdown by period"""
    conn = get_db_connection()
    if not conn:
        return {"today": 0, "week": 0, "month": 0, "total": 0}

    cursor = conn.cursor()

    try:
        if USE_POSTGRES:
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) FROM payments
                WHERE status = 'approved' AND verified_at::date = CURRENT_DATE
            """)
            today = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) FROM payments
                WHERE status = 'approved' AND verified_at >= date_trunc('week', CURRENT_DATE)
            """)
            week = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) FROM payments
                WHERE status = 'approved' AND verified_at >= date_trunc('month', CURRENT_DATE)
            """)
            month = cursor.fetchone()[0]

            cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'approved'")
            total = cursor.fetchone()[0]
        else:
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) FROM payments
                WHERE status = 'approved' AND date(verified_at) = date('now')
            """)
            today = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) FROM payments
                WHERE status = 'approved' AND verified_at >= date('now', 'weekday 0', '-7 days')
            """)
            week = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) FROM payments
                WHERE status = 'approved' AND verified_at >= date('now', 'start of month')
            """)
            month = cursor.fetchone()[0]

            cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'approved'")
            total = cursor.fetchone()[0]

        return {"today": today, "week": week, "month": month, "total": total}
    except Exception as e:
        print(f"Error getting revenue stats: {e}")
        return {"today": 0, "week": 0, "month": 0, "total": 0}
    finally:
        cursor.close()
        conn.close()


# ==================== ADMIN: VOCABULARY MANAGEMENT ====================

def update_vocabulary_word(word_id: int, word: str, meaning_bn: str, example: str = "", category: str = "", phonetic: str = "") -> bool:
    """Update an existing vocabulary word"""
    conn = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    try:
        if USE_POSTGRES:
            cursor.execute("""
                UPDATE vocabulary SET word = %s, meaning_bn = %s, example = %s, category = %s, phonetic = %s
                WHERE id = %s
            """, (word, meaning_bn, example, category, phonetic, word_id))
        else:
            cursor.execute("""
                UPDATE vocabulary SET word = ?, meaning_bn = ?, example = ?, category = ?, phonetic = ?
                WHERE id = ?
            """, (word, meaning_bn, example, category, phonetic, word_id))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error updating word: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def delete_vocabulary_word(word_id: int) -> bool:
    """Delete a vocabulary word"""
    conn = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    try:
        if USE_POSTGRES:
            cursor.execute("DELETE FROM vocabulary WHERE id = %s", (word_id,))
        else:
            cursor.execute("DELETE FROM vocabulary WHERE id = ?", (word_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error deleting word: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def search_vocabulary(query: str = "", category: str = "all") -> list:
    """Search and filter vocabulary"""
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor()

    try:
        base_query = "SELECT * FROM vocabulary WHERE 1=1"
        params = []

        if query:
            if USE_POSTGRES:
                base_query += " AND (word ILIKE %s OR meaning_bn ILIKE %s)"
            else:
                base_query += " AND (word LIKE ? OR meaning_bn LIKE ?)"
            q = f"%{query}%"
            params.extend([q, q])

        if category and category != "all":
            if USE_POSTGRES:
                base_query += " AND LOWER(category) LIKE LOWER(%s)"
            else:
                base_query += " AND LOWER(category) LIKE LOWER(?)"
            params.append(f"%{category}%")

        base_query += " ORDER BY word ASC"

        cursor.execute(base_query, params)
        words = cursor.fetchall()
        return _rows_to_dicts(cursor, words)
    except Exception as e:
        print(f"Error searching vocabulary: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


# ==================== ADMIN: ANALYTICS ====================

def get_user_growth(days: int = 30) -> list:
    """Get daily signup counts for the last N days"""
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor()

    try:
        if USE_POSTGRES:
            cursor.execute("""
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM users
                WHERE created_at >= CURRENT_DATE - INTERVAL '%s days'
                GROUP BY DATE(created_at)
                ORDER BY date
            """, (days,))
        else:
            cursor.execute("""
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM users
                WHERE created_at >= date('now', ? || ' days')
                GROUP BY DATE(created_at)
                ORDER BY date
            """, (f"-{days}",))

        rows = cursor.fetchall()
        return [{"date": str(r[0]), "count": r[1]} for r in rows]
    except Exception as e:
        print(f"Error getting user growth: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def get_activity_stats() -> dict:
    """Get active/inactive user breakdown"""
    conn = get_db_connection()
    if not conn:
        return {"active_today": 0, "active_week": 0, "active_month": 0, "inactive": 0}

    cursor = conn.cursor()

    try:
        if USE_POSTGRES:
            cursor.execute("SELECT COUNT(*) FROM users WHERE last_active_date = CURRENT_DATE")
            active_today = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM users WHERE last_active_date >= CURRENT_DATE - 7")
            active_week = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM users WHERE last_active_date >= CURRENT_DATE - 30")
            active_month = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM users WHERE last_active_date < CURRENT_DATE - 30 OR last_active_date IS NULL")
            inactive = cursor.fetchone()[0]
        else:
            cursor.execute("SELECT COUNT(*) FROM users WHERE last_active_date = date('now')")
            active_today = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM users WHERE last_active_date >= date('now', '-7 days')")
            active_week = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM users WHERE last_active_date >= date('now', '-30 days')")
            active_month = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM users WHERE last_active_date < date('now', '-30 days') OR last_active_date IS NULL")
            inactive = cursor.fetchone()[0]

        return {"active_today": active_today, "active_week": active_week, "active_month": active_month, "inactive": inactive}
    except Exception as e:
        print(f"Error getting activity stats: {e}")
        return {"active_today": 0, "active_week": 0, "active_month": 0, "inactive": 0}
    finally:
        cursor.close()
        conn.close()


def get_delivery_stats() -> dict:
    """Get message delivery stats"""
    conn = get_db_connection()
    if not conn:
        return {"total_sent": 0, "users_today": 0}

    cursor = conn.cursor()

    try:
        cursor.execute("SELECT COALESCE(SUM(total_words_sent), 0) FROM users")
        total_sent = cursor.fetchone()[0]

        if USE_POSTGRES:
            cursor.execute("SELECT COUNT(*) FROM users WHERE last_active_date = CURRENT_DATE")
        else:
            cursor.execute("SELECT COUNT(*) FROM users WHERE last_active_date = date('now')")
        users_today = cursor.fetchone()[0]

        return {"total_sent": total_sent, "users_today": users_today}
    except Exception as e:
        print(f"Error getting delivery stats: {e}")
        return {"total_sent": 0, "users_today": 0}
    finally:
        cursor.close()
        conn.close()


def get_top_users(limit: int = 10) -> list:
    """Get top users by streak"""
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor()

    try:
        if USE_POSTGRES:
            cursor.execute("""
                SELECT name, email, streak_days, words_learned, total_words_sent
                FROM users WHERE is_admin = FALSE
                ORDER BY streak_days DESC LIMIT %s
            """, (limit,))
        else:
            cursor.execute("""
                SELECT name, email, streak_days, words_learned, total_words_sent
                FROM users WHERE is_admin = 0
                ORDER BY streak_days DESC LIMIT ?
            """, (limit,))

        users = cursor.fetchall()
        return [{"name": u[0], "email": u[1], "streak": u[2] or 0, "words_learned": u[3] or 0, "words_sent": u[4] or 0} for u in users]
    except Exception as e:
        print(f"Error getting top users: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def get_vocab_category_stats() -> dict:
    """Get vocabulary count by category (supports comma-separated multi-category)"""
    conn = get_db_connection()
    if not conn:
        return {}

    cursor = conn.cursor()

    try:
        cursor.execute("SELECT category FROM vocabulary")
        rows = cursor.fetchall()
        counts = {}
        for row in rows:
            cats = [c.strip().lower() for c in (row[0] or '').split(',') if c.strip()]
            for cat in cats:
                if cat:
                    counts[cat] = counts.get(cat, 0) + 1
        return counts
    except Exception as e:
        print(f"Error getting vocab category stats: {e}")
        return {}
    finally:
        cursor.close()
        conn.close()


# ==================== QUIZ ====================

def get_learned_words(user_id: int, category: str = None, count: int = 10, use_user_category: bool = True) -> list:
    """Get random words for quiz. category=None + use_user_category=True uses user's preference."""
    conn = get_db_connection()
    if not conn:
        return []
    cursor = conn.cursor()

    # Get user's last_word_index and preferred category
    if USE_POSTGRES:
        cursor.execute("SELECT last_word_index, preferred_category FROM users WHERE id = %s", (user_id,))
    else:
        cursor.execute("SELECT last_word_index, preferred_category FROM users WHERE id = ?", (user_id,))

    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        return []

    last_index = row[0] or 0

    # Determine category filter
    if use_user_category and not category:
        category = row[1] or ""

    # Get random words
    if category:
        cat_pattern = f"%{category}%"
        if USE_POSTGRES:
            cursor.execute("""
                SELECT id, word, phonetic, meaning_bn, example, category
                FROM vocabulary
                WHERE LOWER(category) LIKE LOWER(%s)
                ORDER BY RANDOM() LIMIT %s
            """, (cat_pattern, count))
        else:
            cursor.execute("""
                SELECT id, word, phonetic, meaning_bn, example, category
                FROM vocabulary
                WHERE LOWER(category) LIKE LOWER(?)
                ORDER BY RANDOM() LIMIT ?
            """, (cat_pattern, count))
    else:
        if USE_POSTGRES:
            cursor.execute("""
                SELECT id, word, phonetic, meaning_bn, example, category
                FROM vocabulary ORDER BY RANDOM() LIMIT %s
            """, (count,))
        else:
            cursor.execute("""
                SELECT id, word, phonetic, meaning_bn, example, category
                FROM vocabulary ORDER BY RANDOM() LIMIT ?
            """, (count,))

    rows = cursor.fetchall()
    words = _rows_to_dicts(cursor, rows)
    cursor.close()
    conn.close()
    return words


def get_wrong_options(correct_id: int, category: str = None, count: int = 3) -> list:
    """Get random wrong meaning options for quiz"""
    conn = get_db_connection()
    if not conn:
        return []
    cursor = conn.cursor()

    if category:
        cat_pattern = f"%{category}%"
        if USE_POSTGRES:
            cursor.execute("""
                SELECT meaning_bn FROM vocabulary
                WHERE id != %s AND LOWER(category) LIKE LOWER(%s)
                ORDER BY RANDOM() LIMIT %s
            """, (correct_id, cat_pattern, count))
        else:
            cursor.execute("""
                SELECT meaning_bn FROM vocabulary
                WHERE id != ? AND LOWER(category) LIKE LOWER(?)
                ORDER BY RANDOM() LIMIT ?
            """, (correct_id, cat_pattern, count))
    else:
        if USE_POSTGRES:
            cursor.execute("""
                SELECT meaning_bn FROM vocabulary
                WHERE id != %s ORDER BY RANDOM() LIMIT %s
            """, (correct_id, count))
        else:
            cursor.execute("""
                SELECT meaning_bn FROM vocabulary
                WHERE id != ? ORDER BY RANDOM() LIMIT ?
            """, (correct_id, count))

    options = [r[0] for r in cursor.fetchall()]
    cursor.close()
    conn.close()
    return options


def get_wrong_english_words(correct_id: int, category: str = None, count: int = 3) -> list:
    """Get random wrong English word options for reverse quiz"""
    conn = get_db_connection()
    if not conn:
        return []
    cursor = conn.cursor()

    if category:
        cat_pattern = f"%{category}%"
        if USE_POSTGRES:
            cursor.execute("""
                SELECT word FROM vocabulary
                WHERE id != %s AND LOWER(category) LIKE LOWER(%s)
                ORDER BY RANDOM() LIMIT %s
            """, (correct_id, cat_pattern, count))
        else:
            cursor.execute("""
                SELECT word FROM vocabulary
                WHERE id != ? AND LOWER(category) LIKE LOWER(?)
                ORDER BY RANDOM() LIMIT ?
            """, (correct_id, cat_pattern, count))
    else:
        if USE_POSTGRES:
            cursor.execute("""
                SELECT word FROM vocabulary
                WHERE id != %s ORDER BY RANDOM() LIMIT %s
            """, (correct_id, count))
        else:
            cursor.execute("""
                SELECT word FROM vocabulary
                WHERE id != ? ORDER BY RANDOM() LIMIT ?
            """, (correct_id, count))

    options = [r[0] for r in cursor.fetchall()]
    cursor.close()
    conn.close()
    return options


def update_quiz_score(user_id: int, score: int) -> dict:
    """Update quiz high score if new score is higher"""
    conn = get_db_connection()
    if not conn:
        return {"success": False}
    cursor = conn.cursor()

    if USE_POSTGRES:
        cursor.execute("SELECT quiz_high_score FROM users WHERE id = %s", (user_id,))
    else:
        cursor.execute("SELECT quiz_high_score FROM users WHERE id = ?", (user_id,))

    row = cursor.fetchone()
    current_high = row[0] if row else 0
    new_record = score > current_high

    if new_record:
        if USE_POSTGRES:
            cursor.execute("UPDATE users SET quiz_high_score = %s WHERE id = %s", (score, user_id))
        else:
            cursor.execute("UPDATE users SET quiz_high_score = ? WHERE id = ?", (score, user_id))
        conn.commit()

    cursor.close()
    conn.close()
    return {"success": True, "new_record": new_record, "high_score": max(current_high, score)}


# ==================== WEEKLY QUIZ CONTESTS ====================

def init_contest_tables():
    """Initialize quiz contest tables"""
    conn = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    if USE_POSTGRES:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_contests (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                week_number INTEGER NOT NULL,
                year INTEGER NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                reveal_time TEXT NOT NULL,
                question_count INTEGER DEFAULT 25,
                status TEXT DEFAULT 'upcoming',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contest_questions (
                id SERIAL PRIMARY KEY,
                contest_id INTEGER NOT NULL,
                question_number INTEGER NOT NULL,
                question_type TEXT NOT NULL,
                word_id INTEGER,
                word TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                options TEXT NOT NULL,
                phonetic TEXT,
                FOREIGN KEY (contest_id) REFERENCES quiz_contests(id),
                UNIQUE(contest_id, question_number)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_participations (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                contest_id INTEGER NOT NULL,
                score INTEGER NOT NULL,
                correct_count INTEGER NOT NULL,
                wrong_count INTEGER NOT NULL,
                skipped_count INTEGER DEFAULT 0,
                time_taken_seconds INTEGER,
                submitted_at TEXT NOT NULL,
                rank INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (contest_id) REFERENCES quiz_contests(id),
                UNIQUE(user_id, contest_id)
            )
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_contests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                week_number INTEGER NOT NULL,
                year INTEGER NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                reveal_time TEXT NOT NULL,
                question_count INTEGER DEFAULT 25,
                status TEXT DEFAULT 'upcoming',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contest_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contest_id INTEGER NOT NULL,
                question_number INTEGER NOT NULL,
                question_type TEXT NOT NULL,
                word_id INTEGER,
                word TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                options TEXT NOT NULL,
                phonetic TEXT,
                FOREIGN KEY (contest_id) REFERENCES quiz_contests(id),
                UNIQUE(contest_id, question_number)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_participations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                contest_id INTEGER NOT NULL,
                score INTEGER NOT NULL,
                correct_count INTEGER NOT NULL,
                wrong_count INTEGER NOT NULL,
                skipped_count INTEGER DEFAULT 0,
                time_taken_seconds INTEGER,
                submitted_at TEXT NOT NULL,
                rank INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (contest_id) REFERENCES quiz_contests(id),
                UNIQUE(user_id, contest_id)
            )
        """)

    conn.commit()
    cursor.close()
    conn.close()
    print("Contest tables initialized!")
    return True


def migrate_contest_fields():
    """Add contest-related fields to users table and contest tables"""
    conn = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    try:
        # Add columns to quiz_contests for weekly contest
        if USE_POSTGRES:
            cursor.execute("ALTER TABLE quiz_contests ADD COLUMN IF NOT EXISTS contest_type TEXT DEFAULT 'daily'")
            cursor.execute("ALTER TABLE quiz_contests ADD COLUMN IF NOT EXISTS time_per_question_seconds INTEGER DEFAULT 0")
        else:
            cursor.execute("PRAGMA table_info(quiz_contests)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'contest_type' not in columns:
                cursor.execute("ALTER TABLE quiz_contests ADD COLUMN contest_type TEXT DEFAULT 'daily'")
            if 'time_per_question_seconds' not in columns:
                cursor.execute("ALTER TABLE quiz_contests ADD COLUMN time_per_question_seconds INTEGER DEFAULT 0")

        if USE_POSTGRES:
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS total_contests_participated INTEGER DEFAULT 0")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS best_contest_rank INTEGER")
        else:
            cursor.execute("PRAGMA table_info(users)")
            columns = [row[1] for row in cursor.fetchall()]

            if 'total_contests_participated' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN total_contests_participated INTEGER DEFAULT 0")

            if 'best_contest_rank' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN best_contest_rank INTEGER")

        conn.commit()
        print("Contest migration completed!")
        return True
    except Exception as e:
        print(f"Contest migration error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def create_contest(name: str, week_number: int, year: int, start_time: str, end_time: str, reveal_time: str, question_count: int = 25, contest_type: str = 'daily', time_per_question_seconds: int = 0) -> Optional[int]:
    """Create a new quiz contest"""
    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor()

    try:
        if USE_POSTGRES:
            cursor.execute("""
                INSERT INTO quiz_contests (name, week_number, year, start_time, end_time, reveal_time, question_count, status, contest_type, time_per_question_seconds)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'upcoming', %s, %s)
                RETURNING id
            """, (name, week_number, year, start_time, end_time, reveal_time, question_count, contest_type, time_per_question_seconds))
            contest_id = cursor.fetchone()[0]
        else:
            cursor.execute("""
                INSERT INTO quiz_contests (name, week_number, year, start_time, end_time, reveal_time, question_count, status, contest_type, time_per_question_seconds)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'upcoming', ?, ?)
            """, (name, week_number, year, start_time, end_time, reveal_time, question_count, contest_type, time_per_question_seconds))
            contest_id = cursor.lastrowid

        conn.commit()
        cursor.close()
        conn.close()
        return contest_id
    except Exception as e:
        print(f"Error creating contest: {e}")
        cursor.close()
        conn.close()
        return None


def get_current_contest() -> Optional[dict]:
    """Get the current or next upcoming contest"""
    conn = get_db_connection()
    if not conn:
        return None
    
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM quiz_contests 
        WHERE status IN ('upcoming', 'active') 
        ORDER BY start_time ASC LIMIT 1
    """)
    
    contest = cursor.fetchone()
    conn.close()
    
    return _row_to_dict(cursor, contest)


def get_contest_by_id(contest_id: int) -> Optional[dict]:
    """Get contest by ID"""
    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    if USE_POSTGRES:
        cursor.execute("SELECT * FROM quiz_contests WHERE id = %s", (contest_id,))
    else:
        cursor.execute("SELECT * FROM quiz_contests WHERE id = ?", (contest_id,))

    contest = cursor.fetchone()
    result = _row_to_dict(cursor, contest)
    cursor.close()
    conn.close()

    return result


def get_completed_contest() -> Optional[dict]:
    """Get the most recent completed contest"""
    conn = get_db_connection()
    if not conn:
        return None
    
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM quiz_contests 
        WHERE status = 'completed' 
        ORDER BY end_time DESC LIMIT 1
    """)
    
    contest = cursor.fetchone()
    conn.close()
    
    return _row_to_dict(cursor, contest)


def update_contest_status(contest_id: int, status: str) -> bool:
    """Update contest status"""
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        if USE_POSTGRES:
            cursor.execute("UPDATE quiz_contests SET status = %s WHERE id = %s", (status, contest_id))
        else:
            cursor.execute("UPDATE quiz_contests SET status = ? WHERE id = ?", (status, contest_id))
        conn.commit()
        success = cursor.rowcount > 0
        cursor.close()
        conn.close()
        return success
    except Exception as e:
        print(f"Error updating contest status: {e}")
        cursor.close()
        conn.close()
        return False


def add_contest_question(contest_id: int, question_number: int, question_type: str, word_id: int, word: str, correct_answer: str, options: list, phonetic: str = "") -> bool:
    """Add a question to a contest"""
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        import json
        options_json = json.dumps(options)
        
        if USE_POSTGRES:
            cursor.execute("""
                INSERT INTO contest_questions (contest_id, question_number, question_type, word_id, word, correct_answer, options, phonetic)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (contest_id, question_number, question_type, word_id, word, correct_answer, options_json, phonetic))
        else:
            cursor.execute("""
                INSERT INTO contest_questions (contest_id, question_number, question_type, word_id, word, correct_answer, options, phonetic)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (contest_id, question_number, question_type, word_id, word, correct_answer, options_json, phonetic))
        
        conn.commit()
        success = cursor.rowcount > 0
        cursor.close()
        conn.close()
        return success
    except Exception as e:
        print(f"Error adding contest question: {e}")
        cursor.close()
        conn.close()
        return False


def get_contest_questions(contest_id: int) -> list:
    """Get all questions for a contest"""
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor()

    if USE_POSTGRES:
        cursor.execute("""
            SELECT * FROM contest_questions
            WHERE contest_id = %s
            ORDER BY question_number ASC
        """, (contest_id,))
    else:
        cursor.execute("""
            SELECT * FROM contest_questions
            WHERE contest_id = ?
            ORDER BY question_number ASC
        """, (contest_id,))

    questions = cursor.fetchall()

    import json
    result = []
    for q in questions:
        q_dict = _row_to_dict(cursor, q)
        q_dict['options'] = json.loads(q_dict['options'])
        result.append(q_dict)

    cursor.close()
    conn.close()
    return result


def shuffle_contest_questions(contest_id: int) -> list:
    """Get shuffled questions for a contest (for taking the quiz)"""
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor()

    if USE_POSTGRES:
        cursor.execute("""
            SELECT * FROM contest_questions
            WHERE contest_id = %s
            ORDER BY RANDOM()
        """, (contest_id,))
    else:
        cursor.execute("""
            SELECT * FROM contest_questions
            WHERE contest_id = ?
            ORDER BY RANDOM()
        """, (contest_id,))

    questions = cursor.fetchall()

    import json
    result = []
    for q in questions:
        q_dict = _row_to_dict(cursor, q)
        q_dict['options'] = json.loads(q_dict['options'])
        result.append(q_dict)

    cursor.close()
    conn.close()
    return result


def check_user_participation(user_id: int, contest_id: int) -> Optional[dict]:
    """Check if user has already participated in a contest"""
    conn = get_db_connection()
    if not conn:
        return None
    
    cursor = conn.cursor()

    if USE_POSTGRES:
        cursor.execute("""
            SELECT * FROM quiz_participations
            WHERE user_id = %s AND contest_id = %s
        """, (user_id, contest_id))
    else:
        cursor.execute("""
            SELECT * FROM quiz_participations
            WHERE user_id = ? AND contest_id = ?
        """, (user_id, contest_id))
    
    participation = cursor.fetchone()
    conn.close()

    return _row_to_dict(cursor, participation)


def save_contest_participation(user_id: int, contest_id: int, score: int, correct_count: int, wrong_count: int, skipped_count: int, time_taken_seconds: int, submitted_at: str) -> bool:
    """Save user's contest participation and auto-rank"""
    conn = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    try:
        if USE_POSTGRES:
            cursor.execute("""
                INSERT INTO quiz_participations
                (user_id, contest_id, score, correct_count, wrong_count, skipped_count, time_taken_seconds, submitted_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, contest_id, score, correct_count, wrong_count, skipped_count, time_taken_seconds, submitted_at))

            cursor.execute("""
                UPDATE users SET total_contests_participated = total_contests_participated + 1 WHERE id = %s
            """, (user_id,))
        else:
            cursor.execute("""
                INSERT INTO quiz_participations
                (user_id, contest_id, score, correct_count, wrong_count, skipped_count, time_taken_seconds, submitted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, contest_id, score, correct_count, wrong_count, skipped_count, time_taken_seconds, submitted_at))

            cursor.execute("""
                UPDATE users SET total_contests_participated = total_contests_participated + 1 WHERE id = ?
            """, (user_id,))

        conn.commit()
        cursor.close()
        conn.close()

        # Auto-rank after saving
        calculate_and_save_ranks(contest_id)
        return True
    except Exception as e:
        print(f"Error saving participation: {e}")
        cursor.close()
        conn.close()
        return False


def calculate_and_save_ranks(contest_id: int) -> bool:
    """Calculate and save ranks for all participations in a contest"""
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        if USE_POSTGRES:
            cursor.execute("""
                SELECT id FROM quiz_participations
                WHERE contest_id = %s
                ORDER BY score DESC, time_taken_seconds ASC
            """, (contest_id,))
        else:
            cursor.execute("""
                SELECT id FROM quiz_participations
                WHERE contest_id = ?
                ORDER BY score DESC, time_taken_seconds ASC
            """, (contest_id,))

        participations = cursor.fetchall()

        for rank, (p_id,) in enumerate(participations, 1):
            if USE_POSTGRES:
                cursor.execute("""
                    UPDATE quiz_participations SET rank = %s WHERE id = %s
                """, (rank, p_id))
            else:
                cursor.execute("""
                    UPDATE quiz_participations SET rank = ? WHERE id = ?
                """, (rank, p_id))

            if rank <= 10:
                if USE_POSTGRES:
                    cursor.execute("""
                        SELECT user_id FROM quiz_participations WHERE id = %s
                    """, (p_id,))
                else:
                    cursor.execute("""
                        SELECT user_id FROM quiz_participations WHERE id = ?
                    """, (p_id,))
                row = cursor.fetchone()
                if row:
                    user_id = row[0]
                    if USE_POSTGRES:
                        cursor.execute("""
                            SELECT best_contest_rank FROM users WHERE id = %s
                        """, (user_id,))
                    else:
                        cursor.execute("""
                            SELECT best_contest_rank FROM users WHERE id = ?
                        """, (user_id,))
                    current_best = cursor.fetchone()
                    if current_best and (current_best[0] is None or rank < current_best[0]):
                        if USE_POSTGRES:
                            cursor.execute("""
                                UPDATE users SET best_contest_rank = %s WHERE id = %s
                            """, (rank, user_id))
                        else:
                            cursor.execute("""
                                UPDATE users SET best_contest_rank = ? WHERE id = ?
                            """, (rank, user_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error calculating ranks: {e}")
        cursor.close()
        conn.close()
        return False


def get_contest_leaderboard(contest_id: int, limit: int = 100) -> list:
    """Get leaderboard for a contest"""
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor()

    if USE_POSTGRES:
        cursor.execute("""
            SELECT qp.rank, qp.score, qp.correct_count, qp.wrong_count, qp.time_taken_seconds,
                   u.id as user_id, u.name, u.whatsapp_number
            FROM quiz_participations qp
            JOIN users u ON qp.user_id = u.id
            WHERE qp.contest_id = %s AND qp.rank IS NOT NULL
            ORDER BY qp.rank ASC
            LIMIT %s
        """, (contest_id, limit))
    else:
        cursor.execute("""
            SELECT qp.rank, qp.score, qp.correct_count, qp.wrong_count, qp.time_taken_seconds,
                   u.id as user_id, u.name, u.whatsapp_number
            FROM quiz_participations qp
            JOIN users u ON qp.user_id = u.id
            WHERE qp.contest_id = ? AND qp.rank IS NOT NULL
            ORDER BY qp.rank ASC
            LIMIT ?
        """, (contest_id, limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    leaderboard = []
    for row in rows:
        leaderboard.append({
            "rank": row[0],
            "score": row[1],
            "correct": row[2],
            "wrong": row[3],
            "time_seconds": row[4],
            "user_id": row[5],
            "name": row[6],
            "whatsapp": row[7]
        })
    
    return leaderboard


def get_user_contest_rank(user_id: int, contest_id: int) -> Optional[dict]:
    """Get user's rank in a contest"""
    conn = get_db_connection()
    if not conn:
        return None
    
    cursor = conn.cursor()

    if USE_POSTGRES:
        cursor.execute("""
            SELECT qp.rank, qp.score, qp.correct_count, qp.wrong_count, qp.time_taken_seconds,
                   (SELECT COUNT(*) FROM quiz_participations WHERE contest_id = %s AND rank IS NOT NULL) as total_participants
            FROM quiz_participations qp
            WHERE qp.user_id = %s AND qp.contest_id = %s
        """, (contest_id, user_id, contest_id))
    else:
        cursor.execute("""
            SELECT qp.rank, qp.score, qp.correct_count, qp.wrong_count, qp.time_taken_seconds,
                   (SELECT COUNT(*) FROM quiz_participations WHERE contest_id = ? AND rank IS NOT NULL) as total_participants
            FROM quiz_participations qp
            WHERE qp.user_id = ? AND qp.contest_id = ?
        """, (contest_id, user_id, contest_id))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row or row[0] is None:
        return None
    
    return {
        "rank": row[0],
        "score": row[1],
        "correct": row[2],
        "wrong": row[3],
        "time_seconds": row[4],
        "total_participants": row[5],
        "percentile": round((1 - row[0] / row[5]) * 100, 1) if row[5] > 0 else 0
    }


def get_user_contest_history(user_id: int) -> list:
    """Get user's contest participation history"""
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor()

    if USE_POSTGRES:
        cursor.execute("""
            SELECT qc.id, qc.name, qc.week_number, qc.year, qc.start_time, qc.end_time, qc.status,
                   qp.score, qp.correct_count, qp.wrong_count, qp.rank, qp.time_taken_seconds
            FROM quiz_contests qc
            JOIN quiz_participations qp ON qc.id = qp.contest_id
            WHERE qp.user_id = %s
            ORDER BY qc.end_time DESC
        """, (user_id,))
    else:
        cursor.execute("""
            SELECT qc.id, qc.name, qc.week_number, qc.year, qc.start_time, qc.end_time, qc.status,
                   qp.score, qp.correct_count, qp.wrong_count, qp.rank, qp.time_taken_seconds
            FROM quiz_contests qc
            JOIN quiz_participations qp ON qc.id = qp.contest_id
            WHERE qp.user_id = ?
            ORDER BY qc.end_time DESC
        """, (user_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    for row in rows:
        history.append({
            "contest_id": row[0],
            "name": row[1],
            "week": row[2],
            "year": row[3],
            "start_time": row[4],
            "end_time": row[5],
            "status": row[6],
            "score": row[7],
            "correct": row[8],
            "wrong": row[9],
            "rank": row[10],
            "time_seconds": row[11]
        })
    
    return history


def get_top_5_winners(contest_id: int) -> list:
    """Get top 5 winners of a contest for WhatsApp notification"""
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor()

    if USE_POSTGRES:
        cursor.execute("""
            SELECT qp.rank, qp.score, qp.time_taken_seconds,
                   u.id, u.name, u.whatsapp_number
            FROM quiz_participations qp
            JOIN users u ON qp.user_id = u.id
            WHERE qp.contest_id = %s AND qp.rank <= 5 AND qp.rank IS NOT NULL
            ORDER BY qp.rank ASC
        """, (contest_id,))
    else:
        cursor.execute("""
            SELECT qp.rank, qp.score, qp.time_taken_seconds,
                   u.id, u.name, u.whatsapp_number
            FROM quiz_participations qp
            JOIN users u ON qp.user_id = u.id
            WHERE qp.contest_id = ? AND qp.rank <= 5 AND qp.rank IS NOT NULL
            ORDER BY qp.rank ASC
        """, (contest_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    winners = []
    for row in rows:
        winners.append({
            "rank": row[0],
            "score": row[1],
            "time_seconds": row[2],
            "user_id": row[3],
            "name": row[4],
            "whatsapp": row[5]
        })
    
    return winners


def generate_contest_questions(contest_id: int, question_count: int = 25) -> dict:
    """Generate mixed Bengali-English questions for a contest
    
    50% Bengali -> English (word shown in Bengali, pick English word)
    50% English -> Bengali (word shown in English, pick Bengali meaning)
    Uses fallback list from whatsapp_bot if database is empty.
    """
    import json
    import random
    import sys
    import os

    conn = get_db_connection()
    if not conn:
        return {"success": False, "error": "Database error"}
    
    cursor = conn.cursor()
    
    try:
        if USE_POSTGRES:
            cursor.execute("SELECT id, word, meaning_bn, phonetic FROM vocabulary ORDER BY RANDOM() LIMIT %s", (question_count,))
        else:
            cursor.execute("SELECT id, word, meaning_bn, phonetic FROM vocabulary ORDER BY RANDOM() LIMIT ?", (question_count,))
        words = cursor.fetchall()
        
        if len(words) < question_count:
            cursor.close()
            conn.close()
            # Use fallback vocabulary from whatsapp_bot
            try:
                from whatsapp_bot import fallback_vocab_list as fb_list
                fallback_words = fb_list
            except ImportError:
                return {"success": False, "error": f"Not enough vocabulary. Need {question_count}, have {len(words)}"}
            
            if len(fallback_words) < question_count:
                return {"success": False, "error": f"Not enough vocabulary. Need {question_count}, have {len(words)} + {len(fallback_words)}"}
            
            half_count = question_count // 2
            saved = 0
            conn2 = get_db_connection()
            if not conn2:
                return {"success": False, "error": "Database error"}
            cur2 = conn2.cursor()
            
            for i in range(question_count):
                idx = i % len(fallback_words)
                item = fallback_words[idx]
                word = item.get("word", "")
                meaning_bn = item.get("meaning", item.get("meaning_bn", ""))
                phonetic = item.get("phonetic", "")
                
                if i < half_count:
                    question_type = "en_to_bn"
                    correct_answer = meaning_bn
                    wrong_options = []
                    for j, fw in enumerate(fallback_words):
                        if j != idx:
                            wrong_options.append(fw.get("meaning", fw.get("meaning_bn", "")))
                        if len(wrong_options) >= 3:
                            break
                else:
                    question_type = "bn_to_en"
                    correct_answer = word
                    wrong_options = []
                    for j, fw in enumerate(fallback_words):
                        if j != idx:
                            wrong_options.append(fw.get("word", ""))
                        if len(wrong_options) >= 3:
                            break
                
                if len(wrong_options) < 3:
                    continue
                
                options = [correct_answer] + wrong_options[:3]
                random.shuffle(options)
                
                try:
                    if USE_POSTGRES:
                        cur2.execute("""
                            INSERT INTO contest_questions
                            (contest_id, question_number, question_type, word_id, word, correct_answer, options, phonetic)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (contest_id, i + 1, question_type, None, word, correct_answer, json.dumps(options), phonetic or ""))
                    else:
                        cur2.execute("""
                            INSERT INTO contest_questions
                            (contest_id, question_number, question_type, word_id, word, correct_answer, options, phonetic)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (contest_id, i + 1, question_type, None, word, correct_answer, json.dumps(options), phonetic or ""))
                    saved += 1
                except:
                    pass
            
            conn2.commit()
            cur2.close()
            conn2.close()
            return {"success": True, "generated": saved}
        
        half_count = question_count // 2
        saved = 0
        
        for i, word_row in enumerate(words[:question_count]):
            word_id, word, meaning_bn, phonetic = word_row
            
            if i < half_count:
                question_type = "en_to_bn"
                question_text = word
                correct_answer = meaning_bn
                
                if USE_POSTGRES:
                    cursor.execute("""
                        SELECT meaning_bn FROM vocabulary
                        WHERE id != %s ORDER BY RANDOM() LIMIT 3
                    """, (word_id,))
                else:
                    cursor.execute("""
                        SELECT meaning_bn FROM vocabulary
                        WHERE id != ? ORDER BY RANDOM() LIMIT 3
                    """, (word_id,))
                wrong_options = [row[0] for row in cursor.fetchall()]
            else:
                question_type = "bn_to_en"
                question_text = meaning_bn
                correct_answer = word
                
                if USE_POSTGRES:
                    cursor.execute("""
                        SELECT word FROM vocabulary
                        WHERE id != %s ORDER BY RANDOM() LIMIT 3
                    """, (word_id,))
                else:
                    cursor.execute("""
                        SELECT word FROM vocabulary
                        WHERE id != ? ORDER BY RANDOM() LIMIT 3
                    """, (word_id,))
                wrong_options = [row[0] for row in cursor.fetchall()]
            
            if len(wrong_options) < 3:
                continue
            
            options = [correct_answer] + wrong_options
            random.shuffle(options)
            
            try:
                if USE_POSTGRES:
                    cursor.execute("""
                        INSERT INTO contest_questions
                        (contest_id, question_number, question_type, word_id, word, correct_answer, options, phonetic)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (contest_id, i + 1, question_type, word_id, word, correct_answer, json.dumps(options), phonetic or ""))
                else:
                    cursor.execute("""
                        INSERT INTO contest_questions
                        (contest_id, question_number, question_type, word_id, word, correct_answer, options, phonetic)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (contest_id, i + 1, question_type, word_id, word, correct_answer, json.dumps(options), phonetic or ""))
                saved += 1
            except:
                pass
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"success": True, "generated": saved}
        
    except Exception as e:
        print(f"Error generating questions: {e}")
        cursor.close()
        conn.close()
        return {"success": False, "error": str(e)}


def check_and_create_weekly_contest() -> Optional[int]:
    """Check if weekly contest needs to be created and create it"""
    import datetime

    today = datetime.datetime.now()
    weekday = today.weekday()

    friday = today + datetime.timedelta(days=(4 - weekday) % 7)
    friday = friday.replace(hour=0, minute=0, second=0, microsecond=0)

    saturday = friday + datetime.timedelta(days=1, hours=23, minutes=59, seconds=59)
    reveal_time = friday + datetime.timedelta(days=1)

    contest_name = f"Weekly Challenge #{today.isocalendar()[1]}"

    existing = get_current_contest()
    if existing:
        return existing["id"]

    contest_id = create_contest(
        name=contest_name,
        week_number=today.isocalendar()[1],
        year=today.year,
        start_time=friday.isoformat(),
        end_time=saturday.isoformat(),
        reveal_time=reveal_time.isoformat(),
        question_count=25
    )

    if contest_id:
        generate_contest_questions(contest_id, 25)


def ensure_daily_contest() -> Optional[dict]:
    """Ensure today's daily contest exists. Create if not. Returns contest dict."""
    import datetime

    today = datetime.date.today()
    today_str = today.isoformat()

    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor()

    # Check if today's contest already exists
    if USE_POSTGRES:
        cursor.execute("""
            SELECT id, name, question_count, status FROM quiz_contests
            WHERE DATE(start_time) = %s AND name LIKE 'Daily%%'
            LIMIT 1
        """, (today_str,))
    else:
        cursor.execute("""
            SELECT id, name, question_count, status FROM quiz_contests
            WHERE DATE(start_time) = ? AND name LIKE 'Daily%%'
            LIMIT 1
        """, (today_str,))

    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row:
        return {"id": row[0], "name": row[1], "question_count": row[2], "status": row[3]}

    # Create today's contest
    start_time = datetime.datetime.combine(today, datetime.time.min).isoformat()
    end_time = datetime.datetime.combine(today, datetime.time.max).isoformat()
    reveal_time = end_time
    contest_name = f"Daily Challenge - {today.strftime('%b %d, %Y')}"

    contest_id = create_contest(
        name=contest_name,
        week_number=today.isocalendar()[1],
        year=today.year,
        start_time=start_time,
        end_time=end_time,
        reveal_time=reveal_time,
        question_count=25
    )

    if contest_id:
        generate_contest_questions(contest_id, 25)
        # Activate immediately
        update_contest_status(contest_id, 'active')
        return {"id": contest_id, "name": contest_name, "question_count": 25, "status": "active"}

    return None


def ensure_weekly_contest() -> Optional[dict]:
    """Ensure this week's Friday contest exists. Returns contest info with status."""
    import datetime

    today = datetime.date.today()
    is_friday = today.weekday() == 4

    # Find this week's Friday
    days_until_friday = (4 - today.weekday()) % 7
    friday = today + datetime.timedelta(days=days_until_friday)
    friday_str = friday.isoformat()

    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor()

    # Check if this week's contest already exists
    if USE_POSTGRES:
        cursor.execute("""
            SELECT id, name, question_count, status, time_per_question_seconds FROM quiz_contests
            WHERE contest_type = 'weekly' AND DATE(start_time) = %s
            LIMIT 1
        """, (friday_str,))
    else:
        cursor.execute("""
            SELECT id, name, question_count, status, time_per_question_seconds FROM quiz_contests
            WHERE contest_type = 'weekly' AND DATE(start_time) = ?
            LIMIT 1
        """, (friday_str,))

    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row:
        status = "active" if is_friday else "upcoming"
        return {"id": row[0], "name": row[1], "question_count": row[2], "status": status, "time_per_question_seconds": row[4]}

    # Create this week's Friday contest (even if not Friday yet)
    start_time = datetime.datetime.combine(friday, datetime.time.min).isoformat()
    end_time = (datetime.datetime.combine(friday, datetime.time.min) + datetime.timedelta(hours=24)).isoformat()
    reveal_time = end_time
    week_num = friday.isocalendar()[1]
    contest_name = f"Weekly Challenge - Week {week_num}"

    contest_id = create_contest(
        name=contest_name,
        week_number=week_num,
        year=friday.year,
        start_time=start_time,
        end_time=end_time,
        reveal_time=reveal_time,
        question_count=50,
        contest_type='weekly',
        time_per_question_seconds=9
    )

    if contest_id:
        generate_contest_questions(contest_id, 50)
        status = "active" if is_friday else "upcoming"
        if is_friday:
            update_contest_status(contest_id, 'active')
        return {"id": contest_id, "name": contest_name, "question_count": 50, "status": status, "time_per_question_seconds": 9}

    return None


def get_live_leaderboard(contest_id: int, limit: int = 10) -> list:
    """Get live leaderboard with on-the-fly ranking (no stored rank dependency)"""
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor()

    if USE_POSTGRES:
        cursor.execute("""
            SELECT qp.user_id, u.name, qp.score, qp.correct_count, qp.wrong_count, qp.time_taken_seconds
            FROM quiz_participations qp
            JOIN users u ON qp.user_id = u.id
            WHERE qp.contest_id = %s
            ORDER BY qp.score DESC, qp.time_taken_seconds ASC
            LIMIT %s
        """, (contest_id, limit))
    else:
        cursor.execute("""
            SELECT qp.user_id, u.name, qp.score, qp.correct_count, qp.wrong_count, qp.time_taken_seconds
            FROM quiz_participations qp
            JOIN users u ON qp.user_id = u.id
            WHERE qp.contest_id = ?
            ORDER BY qp.score DESC, qp.time_taken_seconds ASC
            LIMIT ?
        """, (contest_id, limit))

    rows = cursor.fetchall()
    conn.close()

    leaderboard = []
    for rank, row in enumerate(rows, 1):
        minutes = row[5] // 60
        seconds = row[5] % 60
        leaderboard.append({
            "rank": rank,
            "user_id": row[0],
            "name": row[1],
            "score": row[2],
            "correct": row[3],
            "wrong": row[4],
            "time_seconds": row[5],
            "time_display": f"{minutes}m {seconds}s"
        })

    return leaderboard


# ==================== LEADERBOARD FUNCTIONS ====================

def reset_weekly_words_if_needed(user_id: int):
    """Reset weekly words counter if a new week has started"""
    conn = get_db_connection()
    if not conn:
        return
    cursor = conn.cursor()
    try:
        today = datetime.now().date()
        if USE_POSTGRES:
            cursor.execute("SELECT week_start_date, weekly_words_learned FROM users WHERE id = %s", (user_id,))
        else:
            cursor.execute("SELECT week_start_date, weekly_words_learned FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            row = _row_to_dict(cursor, row)
            week_start = row.get("week_start_date")
            if week_start:
                if isinstance(week_start, str):
                    week_start = datetime.strptime(week_start, "%Y-%m-%d").date()
                days_since = (today - week_start).days
                if days_since >= 7:
                    if USE_POSTGRES:
                        cursor.execute("UPDATE users SET weekly_words_learned = 0, week_start_date = %s WHERE id = %s", (today, user_id))
                    else:
                        cursor.execute("UPDATE users SET weekly_words_learned = 0, week_start_date = ? WHERE id = ?", (today, user_id))
                    conn.commit()
            else:
                if USE_POSTGRES:
                    cursor.execute("UPDATE users SET week_start_date = %s WHERE id = %s", (today, user_id))
                else:
                    cursor.execute("UPDATE users SET week_start_date = ? WHERE id = ?", (today, user_id))
                conn.commit()
    except Exception as e:
        print(f"Error resetting weekly words: {e}")
    finally:
        cursor.close()
        conn.close()

def reset_monthly_words_if_needed(user_id: int):
    """Reset monthly words counter if a new month has started"""
    conn = get_db_connection()
    if not conn:
        return
    cursor = conn.cursor()
    try:
        today = datetime.now().date()
        if USE_POSTGRES:
            cursor.execute("SELECT month_start_date FROM users WHERE id = %s", (user_id,))
        else:
            cursor.execute("SELECT month_start_date FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            row = _row_to_dict(cursor, row)
            month_start = row.get("month_start_date")
            if month_start:
                if isinstance(month_start, str):
                    month_start = datetime.strptime(month_start, "%Y-%m-%d").date()
                if month_start.month != today.month or month_start.year != today.year:
                    if USE_POSTGRES:
                        cursor.execute("UPDATE users SET monthly_words_learned = 0, month_start_date = %s WHERE id = %s", (today, user_id))
                    else:
                        cursor.execute("UPDATE users SET monthly_words_learned = 0, month_start_date = ? WHERE id = ?", (today, user_id))
                    conn.commit()
            else:
                if USE_POSTGRES:
                    cursor.execute("UPDATE users SET month_start_date = %s WHERE id = %s", (today, user_id))
                else:
                    cursor.execute("UPDATE users SET month_start_date = ? WHERE id = ?", (today, user_id))
                conn.commit()
    except Exception as e:
        print(f"Error resetting monthly words: {e}")
    finally:
        cursor.close()
        conn.close()

def increment_leaderboard_words(user_id: int, count: int = 1):
    """Increment weekly, monthly, and all-time word counters for a user"""
    reset_weekly_words_if_needed(user_id)
    reset_monthly_words_if_needed(user_id)
    conn = get_db_connection()
    if not conn:
        return
    cursor = conn.cursor()
    try:
        today = datetime.now().date()
        if USE_POSTGRES:
            cursor.execute("""
                UPDATE users SET
                    words_learned = words_learned + %s,
                    weekly_words_learned = weekly_words_learned + %s,
                    monthly_words_learned = monthly_words_learned + %s,
                    week_start_date = COALESCE(week_start_date, %s),
                    month_start_date = COALESCE(month_start_date, %s)
                WHERE id = %s
            """, (count, count, count, today, today, user_id))
        else:
            cursor.execute("""
                UPDATE users SET
                    words_learned = words_learned + ?,
                    weekly_words_learned = weekly_words_learned + ?,
                    monthly_words_learned = monthly_words_learned + ?,
                    week_start_date = COALESCE(week_start_date, ?),
                    month_start_date = COALESCE(month_start_date, ?)
                WHERE id = ?
            """, (count, count, count, today, today, user_id))
        conn.commit()
    except Exception as e:
        print(f"Error incrementing leaderboard words: {e}")
    finally:
        cursor.close()
        conn.close()

def get_leaderboard(leaderboard_type: str = "weekly", limit: int = 100) -> list:
    """Get leaderboard rankings"""
    conn = get_db_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    try:
        if leaderboard_type == "weekly":
            order_col = "weekly_words_learned"
        elif leaderboard_type == "monthly":
            order_col = "monthly_words_learned"
        elif leaderboard_type == "streak":
            order_col = "streak_days"
        else:  # all-time
            order_col = "words_learned"

        if USE_POSTGRES:
            cursor.execute(f"""
                SELECT id, name, {order_col} as value
                FROM users WHERE is_subscribed = TRUE AND {order_col} > 0
                ORDER BY {order_col} DESC LIMIT %s
            """, (limit,))
        else:
            cursor.execute(f"""
                SELECT id, name, {order_col} as value
                FROM users WHERE is_subscribed = 1 AND {order_col} > 0
                ORDER BY {order_col} DESC LIMIT ?
            """, (limit,))

        rows = cursor.fetchall()
        leaderboard = []
        for i, row in enumerate(rows):
            row = dict(row)
            leaderboard.append({
                "rank": i + 1,
                "user_id": row["id"],
                "name": row["name"][:1] + "***" if len(row["name"]) > 1 else row["name"],
                "value": row["value"] or 0
            })
        return leaderboard
    except Exception as e:
        print(f"Error getting leaderboard: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_user_leaderboard_rank(user_id: int) -> dict:
    """Get user's rank in all leaderboard categories"""
    conn = get_db_connection()
    if not conn:
        return {}
    cursor = conn.cursor()
    try:
        result = {}
        for lb_type, col in [("weekly", "weekly_words_learned"), ("monthly", "monthly_words_learned"), ("streak", "streak_days"), ("all_time", "words_learned")]:
            if USE_POSTGRES:
                cursor.execute(f"SELECT {col} FROM users WHERE id = %s", (user_id,))
            else:
                cursor.execute(f"SELECT {col} FROM users WHERE id = ?", (user_id,))
            user_row = cursor.fetchone()
            user_val = dict(user_row)[col] if user_row else 0

            if USE_POSTGRES:
                cursor.execute(f"SELECT COUNT(*) as cnt FROM users WHERE is_subscribed = TRUE AND {col} > %s", (user_val,))
            else:
                cursor.execute(f"SELECT COUNT(*) as cnt FROM users WHERE is_subscribed = 1 AND {col} > ?", (user_val,))
            rank_row = cursor.fetchone()
            rank = dict(rank_row)["cnt"] + 1 if rank_row else 1

            result[lb_type] = {"rank": rank, "value": user_val or 0}
        return result
    except Exception as e:
        print(f"Error getting user leaderboard rank: {e}")
        return {}
    finally:
        cursor.close()
        conn.close()


# ==================== CHAT FUNCTIONS ====================

def save_chat_message(user_id: int, role: str, content: str, persona: str = "tutor") -> Optional[int]:
    """Save a chat message and return its ID"""
    conn = get_db_connection()
    if not conn:
        return None
    cursor = conn.cursor()
    try:
        if USE_POSTGRES:
            cursor.execute("""
                INSERT INTO chat_messages (user_id, role, content, persona)
                VALUES (%s, %s, %s, %s) RETURNING id
            """, (user_id, role, content, persona))
            msg_id = cursor.fetchone()[0]
        else:
            cursor.execute("""
                INSERT INTO chat_messages (user_id, role, content, persona)
                VALUES (?, ?, ?, ?)
            """, (user_id, role, content, persona))
            msg_id = cursor.lastrowid
        conn.commit()
        return msg_id
    except Exception as e:
        print(f"Error saving chat message: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_chat_history(user_id: int, limit: int = 50, persona: str = None) -> list:
    """Get chat history for a user"""
    conn = get_db_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    try:
        if persona:
            if USE_POSTGRES:
                cursor.execute("""
                    SELECT id, role, content, persona, created_at FROM chat_messages
                    WHERE user_id = %s AND persona = %s
                    ORDER BY created_at DESC LIMIT %s
                """, (user_id, persona, limit))
            else:
                cursor.execute("""
                    SELECT id, role, content, persona, created_at FROM chat_messages
                    WHERE user_id = ? AND persona = ?
                    ORDER BY created_at DESC LIMIT ?
                """, (user_id, persona, limit))
        else:
            if USE_POSTGRES:
                cursor.execute("""
                    SELECT id, role, content, persona, created_at FROM chat_messages
                    WHERE user_id = %s ORDER BY created_at DESC LIMIT %s
                """, (user_id, limit))
            else:
                cursor.execute("""
                    SELECT id, role, content, persona, created_at FROM chat_messages
                    WHERE user_id = ? ORDER BY created_at DESC LIMIT ?
                """, (user_id, limit))

        rows = cursor.fetchall()
        messages = _rows_to_dicts(cursor, rows)
        messages.reverse()  # oldest first
        return messages
    except Exception as e:
        print(f"Error getting chat history: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_chat_context(user_id: int, limit: int = 20, persona: str = "tutor") -> list:
    """Get recent chat messages formatted as API context"""
    conn = get_db_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    try:
        if USE_POSTGRES:
            cursor.execute("""
                SELECT role, content FROM chat_messages
                WHERE user_id = %s AND persona = %s
                ORDER BY created_at DESC LIMIT %s
            """, (user_id, persona, limit))
        else:
            cursor.execute("""
                SELECT role, content FROM chat_messages
                WHERE user_id = ? AND persona = ?
                ORDER BY created_at DESC LIMIT ?
            """, (user_id, persona, limit))

        rows = cursor.fetchall()
        messages = [{"role": r.get("role", r[0]) if isinstance(r, dict) else r[0], "content": r.get("content", r[1]) if isinstance(r, dict) else r[1]} for r in rows]
        messages.reverse()
        return messages
    except Exception as e:
        print(f"Error getting chat context: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def clear_chat_history(user_id: int, persona: str = None) -> bool:
    """Clear chat history for a user"""
    conn = get_db_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        if persona:
            if USE_POSTGRES:
                cursor.execute("DELETE FROM chat_messages WHERE user_id = %s AND persona = %s", (user_id, persona))
            else:
                cursor.execute("DELETE FROM chat_messages WHERE user_id = ? AND persona = ?", (user_id, persona))
        else:
            if USE_POSTGRES:
                cursor.execute("DELETE FROM chat_messages WHERE user_id = %s", (user_id,))
            else:
                cursor.execute("DELETE FROM chat_messages WHERE user_id = ?", (user_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error clearing chat history: {e}")
        return False
    finally:
        cursor.close()
        conn.close()
    
    return contest_id