import os
import sqlite3
import random
import string
import threading
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import telebot

# Configurations
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
WEBAPP_URL = os.environ.get("WEBAPP_URL", "https://mela-sacco.onrender.com")
SUPER_ADMIN_ID = os.environ.get("SUPER_ADMIN_ID", "5351353727")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__, static_folder='.')
CORS(app)

DB_FILE = "mela_sacco.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            pin TEXT NOT NULL,
            role TEXT NOT NULL,
            category TEXT DEFAULT 'Pending Registration'
        )
    ''')
    
    # OTP Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS otps (
            user_id TEXT PRIMARY KEY,
            otp_code TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Audit Transparency Log Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            performed_by TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Default Super Admin setup using provided Telegram ID
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (SUPER_ADMIN_ID,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id, name, pin, role, category) VALUES (?, ?, ?, ?, ?)",
                       (SUPER_ADMIN_ID, 'Main Super Admin', '123456', 'super_admin', 'Shareholders'))
        
    conn.commit()
    conn.close()

init_db()

# Serve Frontend HTML
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# --- Telegram Bot Handler ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.InlineKeyboardMarkup()
    btn = telebot.types.InlineKeyboardButton(
        text="🚀 Open Mela Sacco App", 
        web_app=telebot.types.WebAppInfo(url=WEBAPP_URL)
    )
    markup.add(btn)
    bot.reply_to(
        message, 
        "እንኳን ወደ Mela Sacco ሲስተም በሰላም መጡ! እባክዎን ከታች ያለውን አዝራር በመንካት መተግበሪያውን ይክፈቱ።", 
        reply_markup=markup
    )

# --- Flask REST API Endpoints ---
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json or {}
    user_id = str(data.get('user_id'))
    pin = str(data.get('pin'))

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, name, role, category FROM users WHERE user_id = ? AND pin = ?", (user_id, pin))
    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify({
            'status': 'success',
            'user': {
                'user_id': user[0],
                'name': user[1],
                'role': user[2],
                'category': user[3]
            }
        })
    return jsonify({'status': 'error', 'message': 'የተሳሳተ መለያ ወይም PIN!'}), 401

@app.route('/api/admin/generate-otp', methods=['POST'])
def generate_otp():
    data = request.json or {}
    target_user = str(data.get('target_user'))

    otp = ''.join(random.choices(string.digits, k=6))
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("REPLACE INTO otps (user_id, otp_code) VALUES (?, ?)", (target_user, otp))
    cursor.execute("INSERT INTO audit_logs (action, performed_by) VALUES (?, ?)", 
                   (f"Generated OTP for {target_user}", "super_admin"))
    conn.commit()
    conn.close()

    return jsonify({'status': 'success', 'otp': otp})

@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    data = request.json or {}
    user_id = str(data.get('user_id'))
    otp = str(data.get('otp'))
    new_pin = str(data.get('new_pin'))

    if not new_pin or len(new_pin) != 6:
        return jsonify({'status': 'error', 'message': 'PIN 6 አሃዝ መሆን አለበት!'}), 400

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT otp_code FROM otps WHERE user_id = ?", (user_id,))
    record = cursor.fetchone()

    if record and record[0] == otp:
        cursor.execute("UPDATE users SET pin = ? WHERE user_id = ?", (new_pin, user_id))
        cursor.execute("DELETE FROM otps WHERE user_id = ?", (user_id,))
        cursor.execute("INSERT INTO audit_logs (action, performed_by) VALUES (?, ?)", 
                       ("Reset PIN via OTP", user_id))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success', 'message': 'PIN በስኬት ተቀይሯል!'})
    
    conn.close()
    return jsonify({'status': 'error', 'message': 'የተሳሳተ OTP code!'}), 400

# Execution Loop for Polling
def start_bot():
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print(f"Bot Polling Error: {e}")

if __name__ == '__main__':
    # Start bot polling in a background thread
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    
    # Run Flask Web Server on assigned Port
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
