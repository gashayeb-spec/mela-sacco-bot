import json
import logging
import os
import sqlite3
import base64
import random
import asyncio
from io import BytesIO
from threading import Thread
from flask import Flask, request, jsonify
from flask_cors import CORS
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Credentials
BOT_TOKEN = os.getenv("BOT_TOKEN", "8543715567:AAFiBZK911QHVYC_UEq3pztxhyitTsU8g1M")
SUPER_ADMIN_ID = int(os.getenv("ADMIN_CHAT_ID", "5351353727"))
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://gashayeb-spec.github.io/mela-sacco-bot/?v=14.0")
PORT = int(os.environ.get("PORT", 10000))

app = Flask(__name__)
CORS(app)

bot_instance = Bot(token=BOT_TOKEN)

# In-Memory OTP Store: { user_id: "123456" }
otp_store = {}

def init_db():
    conn = sqlite3.connect('sacco_database.db')
    cursor = conn.cursor()
    
    # Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            fullname TEXT,
            phone TEXT,
            address TEXT,
            national_id TEXT,
            tin TEXT,
            vat TEXT,
            doc_status TEXT DEFAULT 'Pending Verification',
            loan_status TEXT DEFAULT 'None',
            user_type TEXT DEFAULT 'Shareholder',
            password TEXT DEFAULT '123456',
            user_check TEXT,
            guarantor_name TEXT,
            guarantor_phone TEXT,
            guarantor_check TEXT,
            savings REAL DEFAULT 0.0,
            loan_amount REAL DEFAULT 0.0
        )
    ''')
    
    # Staff / Sub-Collectors Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS staff (
            staff_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            role TEXT,
            performance TEXT,
            assigned_by INTEGER
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()
logging.basicConfig(level=logging.INFO)

@app.route('/', methods=['GET'])
def home():
    return "Mela Sacco Backend - Developed by Gashaye Bejigu Herebo. All Rights Reserved.", 200

# OTP Generation Endpoint
@app.route('/api/request-otp', methods=['POST'])
def request_otp():
    data = request.json
    user_id = data.get("user_id")
    role = data.get("role", "User")
    
    otp = str(random.randint(100000, 999999))
    otp_store[str(user_id)] = otp
    
    msg = (
        f"🔑 **የፓስወርድ ማደሻ ጥያቄ (OTP Request)**\n\n"
        f"👤 **ተጠቃሚ/አድሚን ID:** `{user_id}`\n"
        f"ከፍል/ሚና: {role}\n\n"
        f"🎲 **የተፈጠረ OTP ቁጥር:** `{otp}`\n\n"
        f"እባክዎን ይህንን OTP ቁጥር ለተጠቃሚው ይላኩለት።"
    )
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(bot_instance.send_message(chat_id=SUPER_ADMIN_ID, text=msg, parse_mode="Markdown"))
    
    return jsonify({"status": "success", "message": "OTP sent to Super Admin"}), 200

# API Data Receiver
@app.route('/api/data', methods=['POST'])
def handle_api_data():
    data = request.json
    action = data.get("action")
    
    conn = sqlite3.connect('sacco_database.db')
    cursor = conn.cursor()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    if action == "register":
        user_id = data.get("userId", "1000")
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, fullname, phone, address, national_id, tin, vat, password, doc_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Pending Verification')
        ''', (user_id, data.get("fullName"), data.get("phone"), data.get("address"), 
              data.get("nationalId"), data.get("tin"), data.get("vat", "N/A"), data.get("password", "123456")))
        conn.commit()

        admin_msg = (
            f"📥 **አዲስ የአባልነት ማመልከቻ ደርሷል!**\n\n"
            f"👤 **ስም:** {data.get('fullName')}\n"
            f"📞 **ስልክ:** `{data.get('phone')}`\n"
            f"🏠 **አድራሻ:** {data.get('address')}\n"
            f"🪪 **ናሽናል አይዲ:** `{data.get('nationalId')}`\n"
            f"🆔 **TIN:** `{data.get('tin')}`\n"
            f"🔢 **ID:** `{user_id}`"
        )
        loop.run_until_complete(bot_instance.send_message(chat_id=SUPER_ADMIN_ID, text=admin_msg, parse_mode="Markdown"))

    elif action == "update_doc_status":
        cursor.execute("UPDATE users SET doc_status=? WHERE user_id=?", (data.get("status"), data.get("targetId")))
        conn.commit()

    elif action == "update_loan_status":
        cursor.execute("UPDATE users SET loan_status=? WHERE user_id=?", (data.get("status"), data.get("targetId")))
        conn.commit()

    elif action == "add_staff":
        cursor.execute("INSERT INTO staff (name, role, performance, assigned_by) VALUES (?, ?, ?, ?)",
                       (data.get("name"), data.get("role"), data.get("performance"), data.get("assigned_by")))
        conn.commit()

    conn.close()
    return jsonify({"status": "success"}), 200

def run_flask():
    app.run(host="0.0.0.0", port=PORT)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 Mela Sacco System ይክፈቱ", web_app=WebAppInfo(url=WEB_APP_URL))]
    ])
    await update.message.reply_text(
        "🏥 **እንኳን ወደ mela-sacco.com በደህና መጡ!**\n"
        "_መላ የብድርና ቁጠባ ኃላፊነቱ የተወሰነ የህብረት ስራ ማህበር_\n\n"
        "ከታች ያለውን አዝራር በመጫን የድርጅቱን አገልግሎት እና ዳሽቦርዶችን ማግኘት ይችላሉ።\n\n"
        "------------------------------------\n"
        "© All Rights Reserved.\n"
        "**Developed by Gashaye Bejigu Herebo**",
        reply_markup=keyboard, parse_mode="Markdown"
    )

def main():
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    bot = ApplicationBuilder().token(BOT_TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
