import json
import logging
import os
import sqlite3
import base64
from io import BytesIO
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

app = Flask(__name__)
@app.route('/')
def health(): return "SACCO Portal Backend is Active!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

BOT_TOKEN = os.getenv("BOT_TOKEN", "8543715567:AAFiBZK911QHVYC_UEq3pztxhyitTsU8g1M")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "5351353727"))
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://gashayeb-spec.github.io/mela-sacco-bot/")

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect('sacco_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            fullname TEXT,
            phone TEXT,
            tin TEXT,
            status TEXT DEFAULT 'Pending',
            savings REAL DEFAULT 0.0,
            loan_amount REAL DEFAULT 0.0,
            loan_due_date TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            admin_id INTEGER PRIMARY KEY
        )
    ''')
    cursor.execute('INSERT OR IGNORE INTO admins (admin_id) VALUES (?)', (ADMIN_CHAT_ID,))
    conn.commit()
    conn.close()

init_db()

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    btn = ReplyKeyboardMarkup([[KeyboardButton("የመላ ሳኮ ፖርታል (Mini App) 🚀", web_app=WebAppInfo(url=WEB_APP_URL))]], resize_keyboard=True)
    await update.message.reply_text("እንኳን ወደ **መላ ሳኮ (Mela SACCO)** በደህና መጡ!\n\nታች ያለውን አዝራር በመጫን የቁጠባ እና ብድር አገልግሎቶችን ያግኙ፦", reply_markup=btn, parse_mode="Markdown")

def b64_to_file(b64_str, name):
    if not b64_str or b64_str == "-": return None
    if ',' in b64_str: b64_str = b64_str.split(',')[1]
    file_bytes = BytesIO(base64.b64decode(b64_str))
    file_bytes.name = f"{name}.jpg"
    return file_bytes

async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = json.loads(update.message.web_app_data.data)
        user = update.effective_user
        action = data.get("action")

        conn = sqlite3.connect('sacco_database.db')
        cursor = conn.cursor()

        if action == "register":
            cursor.execute('INSERT OR REPLACE INTO users (user_id, fullname, phone, tin, status) VALUES (?, ?, ?, ?, ?)',
                           (user.id, data['fullName'], data['phone'], data['tin'], 'Pending'))
            conn.commit()

            await update.message.reply_text("✅ **የአባልነት ማመልከቻዎ በስኬት ደርሶናል!**\nአድሚኖች መርምረው ምላሽ ይሰጡዎታል።")

            admin_msg = (
                f"📥 **አዲስ ማመልከቻ!**\n\n👤 **ስም:** {data['fullName']}\n📞 **ስልክ:** {data['phone']}\n"
                f"🆔 **TIN:** `{data['tin']}`\n🔗 **ID:** `{user.id}`"
            )
            kbd = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Approve", callback_data=f"app_{user.id}"),
                 InlineKeyboardButton("❌ Reject", callback_data=f"rej_{user.id}")]
            ])

            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_msg, parse_mode="Markdown", reply_markup=kbd)
            
            # Send photos to Admin
            for doc_name, key in [("የንግድ ፈቃድ", "license"), ("መታወቂያ", "idDoc"), ("የጉርድ ፎቶ", "photo")]:
                f = b64_to_file(data.get(key), doc_name)
                if f: await context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=f, caption=f"📄 {doc_name} - {data['fullName']}")

        elif action == "update_account":
            target_id = int(data['targetUser'])
            days = int(data.get('days', 0))
            due_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d') if days > 0 else None

            cursor.execute('UPDATE users SET savings = savings + ?, loan_amount = ?, loan_due_date = ? WHERE user_id = ?',
                           (float(data.get('savings', 0)), float(data.get('loan', 0)), due_date, target_id))
            conn.commit()

            await update.message.reply_text(f"✅ ለተጠቃሚ ID `{target_id}` መረጃው በስኬት ተዘምኗል!")
            await context.bot.send_message(chat_id=target_id, text=f"🔔 **አዲስ የሂሳብ ማሳወቂያ!**\n\nየብድር/ቁጠባ ሂሳብዎ በአድሚን ተዘምኗል። እባክዎ በ Mini App ገጽዎ ላይ ያረጋግጡ።")

        elif action == "add_admin":
            new_admin = int(data['newAdminId'])
            cursor.execute('INSERT OR IGNORE INTO admins (admin_id) VALUES (?)', (new_admin,))
            conn.commit()
            await update.message.reply_text(f"👑 ተጠቃሚ ID `{newAdmin}` በስኬት አድሚን ሆኖ ተሾሟል!")

        conn.close()

    except Exception as e:
        logging.error(f"Error: {e}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, user_id = query.data.split("_")[0], int(query.data.split("_")[1])
    conn = sqlite3.connect('sacco_database.db')
    cursor = conn.cursor()

    if action == "app":
        cursor.execute("UPDATE users SET status = 'Approved' WHERE user_id = ?", (user_id,))
        conn.commit()
        await query.edit_message_text(text=f"{query.message.text}\n\n✅ **ሁኔታ፦ አባልነቱ ጽድቋል!**")
        await context.bot.send_message(chat_id=user_id, text="🎉 **እንኳን ደስ አለዎት!** የአባልነት ማመልከቻዎ ጸድቋል።")
    elif action == "rej":
        cursor.execute("UPDATE users SET status = 'Rejected' WHERE user_id = ?", (user_id,))
        conn.commit()
        await query.edit_message_text(text=f"{query.message.text}\n\n❌ **ሁኔታ፦ ማመልከቻው ውድቅ ተደርጓል!**")
        await context.bot.send_message(chat_id=user_id, text="⚠️ **ማሳሰቢያ፦** ማመልከቻዎ ውድቅ ተደርጓል።")

    conn.close()

def main():
    Thread(target=run_flask, daemon=True).start()
    bot = ApplicationBuilder().token(BOT_TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))
    bot.add_handler(CallbackQueryHandler(handle_callback))
    bot.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
