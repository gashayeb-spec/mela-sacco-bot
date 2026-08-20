import sqlite3
import random

DB_NAME = "mela_sacco.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(super_admin_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reg_id TEXT UNIQUE,
            telegram_id INTEGER UNIQUE,
            full_name TEXT,
            phone TEXT,
            tin TEXT,
            national_id TEXT,
            status TEXT DEFAULT 'Pending',
            savings REAL DEFAULT 0.0,
            loan_amount REAL DEFAULT 0.0,
            interest_rate REAL DEFAULT 0.0,
            loan_days INTEGER DEFAULT 0,
            otp TEXT
        )
    ''')
    
    # Admins Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            username TEXT UNIQUE,
            role TEXT
        )
    ''')
    
    # Register Super Admin (GM)
    cursor.execute('''
        INSERT OR IGNORE INTO admins (telegram_id, username, role) 
        VALUES (?, 'SuperGM', 'GM')
    ''', (super_admin_id,))
    
    conn.commit()
    conn.close()

def register_user(data):
    conn = get_connection()
    cursor = conn.cursor()
    reg_id = "MS-" + str(random.randint(10000, 99999))
    cursor.execute('''
        INSERT INTO users (reg_id, telegram_id, full_name, phone, tin, national_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (reg_id, data['telegram_id'], data['full_name'], data['phone'], data.get('tin'), data.get('national_id')))
    conn.commit()
    conn.close()
    return reg_id

def get_user(telegram_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def update_user_status(telegram_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET status = ? WHERE telegram_id = ?', (telegram_id,))
    conn.commit()
    conn.close()

def update_loan(telegram_id, amount, interest, days):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users SET loan_amount = ?, interest_rate = ?, loan_days = ? 
        WHERE telegram_id = ?
    ''', (amount, interest, days, telegram_id))
    conn.commit()
    conn.close()

def save_otp(telegram_id, otp):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET otp = ? WHERE telegram_id = ?', (telegram_id,))
    conn.commit()
    conn.close()
