import os
import random
import re
import sqlite3
import threading
import requests
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

# Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN", "8543715567:AAHU9BLxEr7rsBDYaTU_d64M2MxfpHOyJYo")
SUPER_ADMIN_ID = os.getenv("SUPER_ADMIN_ID", "5351353727")
WEB_APP_URL = "https://mela-sacco-bot.onrender.com"  # Render Web App URL

# Database Initialization
def init_db():
    conn = sqlite3.connect("mela_sacco.db")
    cursor = conn.cursor()
    
    # Customer / Member Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id TEXT UNIQUE,
            full_name TEXT,
            phone TEXT,
            city TEXT,
            national_id TEXT,
            tin_number TEXT,
            vat_registered TEXT,
            role TEXT DEFAULT 'pending_registration',
            level INTEGER DEFAULT 1,
            password TEXT,
            documents_status TEXT DEFAULT 'pending_verification'
        )
    ''')
    
    # Department & Staff Credentials Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS department_passwords (
            dept_name TEXT PRIMARY KEY,
            password TEXT,
            full_name TEXT,
            phone TEXT,
            role TEXT
        )
    ''')
    
    # Default Department Credentials Setup
    default_depts = [
        ('super_admin', 'admin123', 'Super Admin Master', '0911000000', 'super_admin'),
        ('loan_dept', 'loan123', 'Loan Manager', '0911000001', 'loan_dept'),
        ('doc_verification', 'doc123', 'Verification Officer', '0911000002', 'doc_verification'),
        ('daily_collection', 'daily123', 'Daily Collector', '0911000003', 'daily_collection'),
        ('wm_collection', 'wm123', 'WM Collector', '0911000004', 'wm_collection'),
        ('finance_treasury', 'fin123', 'Finance Head', '0911000005', 'finance_treasury')
    ]
    cursor.executemany("INSERT OR IGNORE INTO department_passwords VALUES (?, ?, ?, ?, ?)", default_depts)

    # OTP Requests Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS otp_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id TEXT,
            otp_code TEXT,
            status TEXT DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # System Audit Logs Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT,
            performed_by TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

# Flask App Setup
app = Flask(__name__)
CORS(app)

def send_telegram_msg(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram Notification Error: {e}")

# API: Normal Customer Registration
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    full_name = data.get('full_name', '').strip()
    phone = data.get('phone', '').strip()
    city = data.get('city', '').strip()
    national_id = data.get('national_id', '').strip()
    tin_number = data.get('tin_number', '').strip()
    vat_registered = data.get('vat_registered', 'no')
    password = data.get('password', '')
    telegram_id = str(data.get('telegram_id', ''))

    phone_pattern = re.compile(r'^(?:\+251|251|09|07)\d{8}$')
    if not phone_pattern.match(phone):
        return jsonify({"status": "error", "message": "እባክዎን ትክክለኛ የኢትዮጵያ ስልክ ቁጥር ያስገቡ! (+251/09/07)"}), 400

    if not (national_id.isdigit() and len(national_id) == 12):
        return jsonify({"status": "error", "message": "ብሔራዊ መታወቂያ (FAN) በትክክል 12 አሃዝ መሆን አለበት!"}), 400

    if not (tin_number.isdigit() and len(tin_number) == 10):
        return jsonify({"status": "error", "message": "የቲን ቁጥር (TIN Number) በትክክል 10 አሃዝ መሆን አለበት!"}), 400

    if len(str(password)) < 6:
        return jsonify({"status": "error", "message": "የይለፍ ቃል ቢያንስ 6 አሃዝ መሆን አለበት!"}), 400

    try:
        conn = sqlite3.connect("mela_sacco.db")
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (telegram_id, full_name, phone, city, national_id, tin_number, vat_registered, password, role, documents_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending_registration', 'pending_verification')
        ''', (telegram_id, full_name, phone, city, national_id, tin_number, vat_registered, password))
        conn.commit()
        conn.close()

        msg = f"<b>🆕 አዲስ የአባልነት ምዝገባ ጥያቄ!</b>\n\n👤 ስም: {full_name}\n📞 ስልክ: {phone}\n📍 ቦታ: {city}\n🆔 FAN: {national_id}\n📄 TIN: {tin_number}"
        send_telegram_msg(SUPER_ADMIN_ID, msg)

        return jsonify({"status": "success", "message": "ምዝገባዎ ተጠናቅቋል! ሰነዶችዎ ተረጋግተው እስኪፀድቁ ድረስ ይቆዩ።"})
    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "message": "ይህ የቴሌግራም መለያ ወይም ስልክ ቁጥር አስቀድሞ ተመዝግቧል!"}), 400

# API: Sub-Admin / Staff Registration (Exclusively by Super Admin)
@app.route('/api/admin/create-staff', methods=['POST'])
def create_staff():
    data = request.json
    name = data.get('name', '').strip()
    phone = data.get('phone', '').strip()
    role = data.get('role', '').strip()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not name or not phone or not username or not password or not role:
        return jsonify({"status": "error", "message": "እባክዎን ሁሉንም መረጃዎች በትክክል ይሙሉ!"}), 400

    try:
        conn = sqlite3.connect("mela_sacco.db")
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO department_passwords (dept_name, password, full_name, phone, role) VALUES (?, ?, ?, ?, ?)",
            (username, password, name, phone, role)
        )
        
        cursor.execute(
            "INSERT INTO system_logs (action, performed_by) VALUES (?, ?)", 
            (f"Created staff account: {username} ({role}) - Phone: {phone} - Name: {name}", "super_admin")
        )
        
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": f"ሰራተኛው '{name}' በ Admin ID '{username}' በትክክል ተመዝግቧል!"})
    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "message": "ይህ Admin ID/Username አስቀድሞ ስራ ላይ ውሏል!"}), 400

# API: Department Staff & Customer Login Separator
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    login_id = data.get('login_id', '').strip()
    password = data.get('password', '').strip()

    conn = sqlite3.connect("mela_sacco.db")
    cursor = conn.cursor()

    # 1. Check if login credentials belong to Staff / Admin
    cursor.execute("SELECT dept_name, role, full_name FROM department_passwords WHERE dept_name=? AND password=?", (login_id, password))
    dept = cursor.fetchone()
    if dept:
        conn.close()
        return jsonify({
            "status": "success", 
            "type": "department", 
            "username": dept[0],
            "role": dept[1],
            "full_name": dept[2]
        })

    # 2. Check if login credentials belong to Normal Customer
    cursor.execute("SELECT id, full_name, role, level, documents_status FROM users WHERE (telegram_id=? OR phone=?) AND password=?", (login_id, login_id, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify({
            "status": "success",
            "type": "member",
            "user": {
                "id": user[0],
                "name": user[1],
                "role": user[2],
                "level": user[3],
                "doc_status": user[4]
            }
        })

    return jsonify({"status": "error", "message": "የተሳሳተ መለያ ቁጥር ወይም የይለፍ ቃል!"}), 401

# API: OTP Request
@app.route('/api/request-otp', methods=['POST'])
def request_otp():
    data = request.json
    telegram_id = data.get('telegram_id', '').strip()

    otp = str(random.randint(100000, 999999))
    conn = sqlite3.connect("mela_sacco.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO otp_requests (telegram_id, otp_code) VALUES (?, ?)", (telegram_id, otp))
    conn.commit()
    conn.close()

    otp_msg = f"<b>🔐 የ OTP የይለፍ ቃል ጥያቄ!</b>\n\n👤 ተጠቃሚ ID: <code>{telegram_id}</code>\n🔑 OTP Code: <code>{otp}</code>"
    send_telegram_msg(SUPER_ADMIN_ID, otp_msg)

    return jsonify({"status": "success", "message": "የ OTP ጥያቄዎ ለ Super Admin ተልኳል።"})

# API: Reset Password via OTP
@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    data = request.json
    telegram_id = data.get('telegram_id', '').strip()
    otp = data.get('otp', '').strip()
    new_password = data.get('new_password', '').strip()

    if len(new_password) < 6:
        return jsonify({"status": "error", "message": "አዲሱ የይለፍ ቃል ቢያንስ 6 አሃዝ መሆን አለበት!"}), 400

    conn = sqlite3.connect("mela_sacco.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM otp_requests WHERE telegram_id=? AND otp_code=? AND status='pending' ORDER BY id DESC LIMIT 1", (telegram_id, otp))
    req = cursor.fetchone()

    if req:
        cursor.execute("UPDATE users SET password=? WHERE telegram_id=?", (new_password, telegram_id))
        cursor.execute("UPDATE otp_requests SET status='used' WHERE id=?", (req[0],))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "የይለፍ ቃልዎ በትክክል ተቀይሯል! አሁን መግባት ይችላሉ።"})

    conn.close()
    return jsonify({"status": "error", "message": "የተሳሳተ ወይም አገልግሎት ላይ የዋለ OTP ኮድ!"}), 400

# Home route: Serves the Web App index.html
@app.route('/')
def home():
    return render_template('index.html')

# Telegram Bot Setup
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="🚀 Mela Sacco Mini App ክፈት", web_app=WebAppInfo(url=WEB_APP_URL))]
    ])
    welcome_text = (
        f"<b>እንኳን ወደ መላ ሳኮ (Mela Sacco) በደህና መጡ! 🏦</b>\n\n"
        f"የአነስተኛ እና መካከለኛ የንግድ እንቅስቃሴዎችን በፋይናንስ ለመደገፍ እና አስተማማኝ የቁጠባና ብድር አገልግሎት በዲጂታል መንገድ ለማቅረብ የተዘጋጀ ሲስተም።\n\n"
        f"ከታች ያለውን በተን በመጫን አገልግሎቱን ማግኘት ይችላሉ።"
    )
    await update.message.reply_text(welcome_text, parse_mode="HTML", reply_markup=keyboard)

def run_flask():
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    # Start Flask Server in a background thread
    threading.Thread(target=run_flask, daemon=True).start()

    # Start Telegram Bot
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    
    print("Mela Sacco Bot & Flask Server Running...")
    application.run_polling()
