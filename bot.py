import json
import logging
import os
import sqlite3
import base64
import asyncio
from io import BytesIO
from threading import Thread
from flask import Flask, request, jsonify
from flask_cors import CORS
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# ሚስጥራዊ መረጃዎች ከ Render Environment Variables እንዲነበቡ ተደርገዋል
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://gashayeb-spec.github.io/mela-sacco-bot/?v=13.0")
PORT = int(os.environ.get("PORT", 10000))

app = Flask(__name__)
CORS(app)

bot_instance = Bot(token=BOT_TOKEN)

def init_db():
    conn = sqlite3.connect('sacco_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            fullname TEXT,
            phone TEXT,
            address TEXT,
            national_id TEXT,
            tin TEXT,
            vat TEXT,
            user_check TEXT,
            guarantor_name TEXT,
            guarantor_phone TEXT,
            guarantor_check TEXT,
            status TEXT DEFAULT 'Pending',
            savings REAL DEFAULT 0.0,
            loan_amount REAL DEFAULT 0.0
        )
    ''')
    conn.commit()
    conn.close()

init_db()
logging.basicConfig(level=logging.INFO)

@app.route('/', methods=['GET'])
def home():
    return "Mela Sacco Bot Server is Online!", 200

@app.route('/api/data', methods=['POST'])
def handle_api_data():
    data = request.json
    action = data.get("action")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    conn = sqlite3.connect('sacco_database.db')
    cursor = conn.cursor()

    if action == "register":
        user_id = data.get("userId", "N/A")
        full_name = data.get("fullName")
        phone = data.get("phone")
        address = data.get("address")
        national_id = data.get("nationalId")
        tin = data.get("tin")
        vat = data.get("vat", "ያልተመዘገበ")

        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, fullname, phone, address, national_id, tin, vat, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id if str(user_id).isdigit() else 1000, full_name, phone, address, national_id, tin, vat, 'Pending'))
        conn.commit()

        admin_msg = (
            f"📥 **አዲስ የአባልነት ማመልከቻ ደርሷል!**\n\n"
            f"👤 **ሙሉ ስም:** {full_name}\n"
            f"📞 **ስልክ ቁጥር:** `{phone}`\n"
            f"🏠 **መኖሪያ አድራሻ:** {address}\n"
            f"🪪 **ናሽናል አይዲ:** `{national_id}`\n"
            f"🆔 **TIN ቁጥር:** `{tin}`\n"
            f"📄 **VAT ቁጥር:** `{vat}`\n"
            f"🔢 **የመዝገብ ID:** `{user_id}`"
        )

        kbd = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Approve", callback_data=f"app_{user_id}"),
             InlineKeyboardButton("❌ Reject", callback_data=f"rej_{user_id}")]
        ])

        if data.get('licenseImg'):
            img_data = base64.b64decode(data['licenseImg'].split(',')[1])
            loop.run_until_complete(bot_instance.send_photo(chat_id=ADMIN_CHAT_ID, photo=BytesIO(img_data), caption=admin_msg, parse_mode="Markdown", reply_markup=kbd))
        else:
            loop.run_until_complete(bot_instance.send_message(chat_id=ADMIN_CHAT_ID, text=admin_msg, parse_mode="Markdown", reply_markup=kbd))

    elif action == "submit_guarantor":
        member_id = int(data['memberId'])
        cursor.execute('''
            UPDATE users SET user_check=?, guarantor_name=?, guarantor_phone=?, guarantor_check=?
            WHERE user_id=?
        ''', (data['userCheck'], data['guarantorName'], data['guarantorPhone'], data['guarantorCheck'], member_id))
        conn.commit()

        guar_msg = (
            f"🤝 **አዲስ የዋስትና ሰነድ ደርሷል!**\n\n"
            f"🔢 **የአባሉ ID:** `{member_id}`\n"
            f"💳 **የተበዳሪው ቼክ No:** `{data['userCheck']}`\n"
            f"👤 **የዋስ ስም:** {data['guarantorName']}\n"
            f"📞 **የዋስ ስልክ:** `{data['guarantorPhone']}`\n"
            f"💳 **የዋስ ቼክ No:** `{data['guarantorCheck']}`"
        )
        loop.run_until_complete(bot_instance.send_message(chat_id=ADMIN_CHAT_ID, text=guar_msg, parse_mode="Markdown"))

    conn.close()
    return jsonify({"status": "success"}), 200

def run_flask():
    app.run(host="0.0.0.0", port=PORT)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 mela-sacco.com ፖርታል ይክፈቱ", web_app=WebAppInfo(url=WEB_APP_URL))]
    ])
    await update.message.reply_text(
        "🏥 **እንኳን ወደ mela-sacco.com በደህና መጡ!**\n"
        "_መላ የብድርና ቁጠባ ኃላፊነቱ የተወሰነ የህብረት ስራ ማህበር_\n\n"
        "ከታች ያለውን አዝራር በመጫን የድርጅቱን አገልግሎቶች ማግኘት ይችላሉ።\n\n"
        "--- \n"
        "የሶፍትዌር አበልጻጊ፦ ጋሻዬ በእጅጉ ®", 
        reply_markup=keyboard, parse_mode="Markdown"
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data_parts = query.data.split("_")
    action, target_id = data_parts[0], data_parts[1]

    conn = sqlite3.connect('sacco_database.db')
    cursor = conn.cursor()

    if action == "app":
        cursor.execute("UPDATE users SET status = 'Approved' WHERE user_id = ?", (target_id,))
        conn.commit()
        await query.message.reply_text(f"✅ የመዝገብ ቁጥር `{target_id}` አባልነቱ ጸድቋል!")
        
        if str(target_id).isdigit():
            try:
                await context.bot.send_message(
                    chat_id=int(target_id),
                    text="🎉 **እንኳን ደስ አለዎት!**\n\nየመላ ህብረት ስራ ማህበር የአባልነት ማመልከቻዎ በአድሚኑ ጸድቋል።"
                )
            except Exception as e:
                logging.error(f"Error: {e}")

    elif action == "rej":
        cursor.execute("UPDATE users SET status = 'Rejected' WHERE user_id = ?", (target_id,))
        conn.commit()
        await query.message.reply_text(f"❌ የመዝገብ ቁጥር `{target_id}` ማመልከቻው ተሰርዟል!")
        
        if str(target_id).isdigit():
            try:
                await context.bot.send_message(
                    chat_id=int(target_id),
                    text="⚠️ **ማሳሰቢያ፦**\n\nየአባልነት ማመልከቻዎ አልጸደቀም።"
                )
            except Exception as e:
                logging.error(f"Error: {e}")

    conn.close()

def main():
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    bot = ApplicationBuilder().token(BOT_TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CallbackQueryHandler(handle_callback))
    bot.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
