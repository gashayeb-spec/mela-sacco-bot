import json
import logging
import os
import sqlite3
import base64
from io import BytesIO
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

app = Flask(__name__)
@app.route('/')
def health(): return "SACCO Portal Backend is Active!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

BOT_TOKEN = os.getenv("BOT_TOKEN", "8543715567:AAFiBZK911QHVYC_UEq3pztxhyitTsU8g1M")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "5351353727"))

# ከታች ባለው መስመር ላይ Cache እንዲጠፋ ?v=3 ተጨምሯል
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://gashayeb-spec.github.io/mela-sacco-bot/?v=3")

def init_db():
    conn = sqlite3.connect('sacco_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            fullname TEXT,
            phone TEXT,
            tin TEXT,
            status TEXT DEFAULT 'NotRegistered',
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
    user_id = update.effective_user.id
    conn = sqlite3.connect('sacco_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT status, savings, loan_amount, loan_due_date FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    status = row[0] if row else 'NotRegistered'
    savings = row[1] if row else 0.0
    loan = row[2] if row else 0.0
    
    days_left = 0
    if row and row[3]:
        try:
            due = datetime.strptime(row[3], '%Y-%m-%d')
            days_left = max(0, (due - datetime.now()).days)
        except: pass

    welcome_text = (
        "🏥 **እንኳን ወደ መላ ህብረት ስራ ማህበር (Mela SACCO) በደህና መጡ!**\n\n"
        "**ይህ ዲጂታል ሲስተም እንዴት ይሰራል?**\n"
        "1️⃣ **ምዝገባ፦** ታች ያለውን አዝራር ተጭነው አስፈላጊ መረጃዎችን (ቲን፣ ንግድ ፈቃድ፣ መታወቂያ) በማስገባት ይመዝገቡ።\n"
        "2️⃣ **ማረጋገጥ (Approval)፦** ያስገቡት መረጃ በአድሚን ተመርምሮ ሲጸድቅ የአባልነት ደረጃዎ **Approved** ይሆናል።\n"
        "3️⃣ **ቁጠባና ብድር፦** እንደ ቁጠባ መጠንዎ እስከ 3 እጥፍ ብድር ማግኘት እና መክፈያ ቀኑን በካሌንደር ቆጣሪ መከታተል ይችላሉ።\n\n"
        "👇 **አገልግሎቱን ለመጀመር ከታች ያለውን አዝራር ይጫኑ፦**"
    )

    user_payload = json.dumps({"status": status, "savings": savings, "loan": loan, "daysLeft": days_left})
    encoded_payload = base64.b64encode(user_payload.encode()).decode()
    dynamic_url = f"{WEB_APP_URL}&tgWebAppStartParam={encoded_payload}" if "?" in WEB_APP_URL else f"{WEB_APP_URL}?tgWebAppStartParam={encoded_payload}"

    # Inline Keyboard
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 የመላ ሳኮ ፖርታል ይክፈቱ", web_app=WebAppInfo(url=dynamic_url))]
    ])
    
    await update.message.reply_text(welcome_text, reply_markup=keyboard, parse_mode="Markdown")

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

        # 1. አባል ሲመዘገብ
        if action == "register":
            cursor.execute('INSERT OR REPLACE INTO users (user_id, fullname, phone, tin, status) VALUES (?, ?, ?, ?, ?)',
                           (user.id, data['fullName'], data['phone'], data['tin'], 'Pending'))
            conn.commit()

            await update.message.reply_text("⏳ **ማመልከቻዎ በስኬት ተልኳል!**\nአድሚኖች መርምረው አፕሩቭ እስኪያደርጉት ድረስ እባክዎ በትዕግስት ይጠብቁ።")

            admin_msg = (
                f"📥 **አዲስ ማመልከቻ!**\n\n👤 **ስም:** {data['fullName']}\n📞 **ስልክ:** {data['phone']}\n"
                f"🆔 **TIN:** `{data['tin']}`\n🔗 **ID:** `{user.id}`"
            )
            kbd = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Approve", callback_data=f"app_{user.id}"),
                 InlineKeyboardButton("❌ Reject", callback_data=f"rej_{user.id}")]
            ])

            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_msg, parse_mode="Markdown", reply_markup=kbd)
            
            for doc_name, key in [("የንግድ ፈቃድ", "license"), ("መታወቂያ", "idDoc"), ("የጉርድ ፎቶ", "photo")]:
                f = b64_to_file(data.get(key), doc_name)
                if f: await context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=f, caption=f"📄 {doc_name} - {data['fullName']}")

        # 2. አድሚኑ መረጃ ሲያዘምን (Update)
        elif action == "update_account":
            target_id = int(data['targetUser'])
            days = int(data.get('days', 0))
            due_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d') if days > 0 else None

            cursor.execute('UPDATE users SET savings = savings + ?, loan_amount = ?, loan_due_date = ? WHERE user_id = ?',
                           (float(data.get('savings', 0)), float(data.get('loan', 0)), due_date, target_id))
            conn.commit()

            await update.message.reply_text(f"✅ **መረጃው ተዘምኗል!**\nተጠቃሚ ID: `{target_id}`\nተጨማሪ ቁጠባ: {data.get('savings')} ETB\nየተፈቀደ ብድር: {data.get('loan')} ETB", parse_mode="Markdown")
            await context.bot.send_message(chat_id=target_id, text=f"🔔 **አዲስ የሂሳብ ማሳወቂያ!**\n\nየብድርና ቁጠባ ሂሳብዎ በአድሚን ተዘምኗል። ቦቱን እንደገና `/start` በማለት አዲሱን ሂሳብዎን ማየት ይችላሉ።")

        # 3. አዲስ አድሚን ሲሾም
        elif action == "add_admin":
            new_admin = int(data['newAdminId'])
            cursor.execute('INSERT OR IGNORE INTO admins (admin_id) VALUES (?)', (new_admin,))
            conn.commit()
            await update.message.reply_text(f"👑 ተጠቃሚ ID `{new_admin}` አድሚን ሆኖ ተሾሟል!")

        # 4. ብሮድካስት ማስታወቂያ ሲላክ
        elif action == "broadcast":
            msg_text = data['message']
            cursor.execute("SELECT user_id FROM users")
            all_users = cursor.fetchall()
            count = 0
            for u in all_users:
                try:
                    await context.bot.send_message(chat_id=u[0], text=f"📢 **የመላ ሳኮ ማስታወቂያ፦**\n\n{msg_text}", parse_mode="Markdown")
                    count += 1
                except: pass
            await update.message.reply_text(f"📢 ማስታወቂያው ለ {count} አባላት በስኬት ተልኳል!")

        conn.close()

    except Exception as e:
        logging.error(f"Error handling WebApp Data: {e}")

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
        await context.bot.send_message(chat_id=user_id, text="🎉 **እንኳን ደስ አለዎት!** የአባልነት ማመልከቻዎ ጸድቋል። ቦቱን እንደገና `/start` በማለት የብድርና ቁጠባ ዳሽቦርድዎን ማየት ይችላሉ።")
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
