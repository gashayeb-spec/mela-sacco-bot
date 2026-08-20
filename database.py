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
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reg_id TEXT UNIQUE,
            telegram_id INTEGER UNIQUE,
            full_name TEXT,
            phone TEXT,
            tin TEXT,
            trade_reg TEXT,
            trade_lic TEXT,
            vat_no TEXT,
            status TEXT DEFAULT 'Pending',
            savings REAL DEFAULT 0.0,
            loan_amount REAL DEFAULT 0.0,
            interest_rate REAL DEFAULT 0.0,
            loan_days INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            username TEXT UNIQUE,
            role TEXT
        )
    ''')
    
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
        INSERT INTO users (reg_id, telegram_id, full_name, phone, tin, trade_reg, trade_lic, vat_no)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        reg_id, 
        data['telegram_id'], 
        data['full_name'], 
        data['phone'], 
        data.get('tin', ''), 
        data.get('trade_reg', ''), 
        data.get('trade_lic', ''), 
        data.get('vat_no', '')
    ))
    conn.commit()
    conn.close()
    return reg_id

def is_admin(telegram_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM admins WHERE telegram_id = ?', (telegram_id,))
    admin = cursor.fetchone()
    conn.close()
    return admin is not None

def get_pending_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE status = 'Pending'")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_user_status(telegram_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET status = ? WHERE telegram_id = ?', (status, telegram_id))
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
