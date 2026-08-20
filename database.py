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
            shares_bought INTEGER DEFAULT 0,
            share_amount REAL DEFAULT 0.0,
            savings REAL DEFAULT 0.0,
            loan_amount REAL DEFAULT 0.0,
            loan_interest REAL DEFAULT 0.0,
            loan_days INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_role TEXT,
            target_id INTEGER,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def register_user(data):
    conn = get_connection()
    cursor = conn.cursor()
    reg_id = "MS-" + str(random.randint(10000, 99999))
    cursor.execute('''
        INSERT INTO users (reg_id, telegram_id, full_name, phone, tin, trade_reg, trade_lic, vat_no)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (reg_id, data['telegram_id'], data['full_name'], data['phone'], data.get('tin', ''), data.get('trade_reg', ''), data.get('trade_lic', ''), data.get('vat_no', '')))
    conn.commit()
    conn.close()
    return reg_id

def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_user_by_tg_id(telegram_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_user_status(telegram_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET status = ? WHERE telegram_id = ?', (status, telegram_id))
    conn.commit()
    conn.close()

def update_member_ledger(data):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users 
        SET shares_bought = ?, share_amount = ?, savings = ?, loan_amount = ?, loan_interest = ?, loan_days = ?
        WHERE telegram_id = ?
    ''', (data['shares_bought'], data['share_amount'], data['savings'], data['loan_amount'], data['loan_interest'], data['loan_days'], data['telegram_id']))
    conn.commit()
    conn.close()

def save_admin_message(sender_role, target_id, message):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO admin_messages (sender_role, target_id, message) VALUES (?, ?, ?)', (sender_role, target_id, message))
    conn.commit()
    conn.close()

def is_admin(telegram_id):
    return True
