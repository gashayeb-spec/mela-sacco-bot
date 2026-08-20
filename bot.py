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
def health(): return "Mela SACCO Backend Active!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

BOT_TOKEN = os.getenv("BOT_TOKEN", "8543715567:AAFiBZK911QHVYC_UEq3pztxhyitTsU8g1M")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "5351353727"))
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://gashayeb-spec.github.io/mela-sacco-bot/?v=6")

def init_db():
    conn = sqlite3.connect('sacco_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            fullname TEXT,
            phone TEXT,
            tin TEXT,
            user_check TEXT,
            guarantor_name TEXT,
            guarantor_phone TEXT,
            guarantor_check TEXT,
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
        "1️⃣ **ምዝገባ፦** አስፈላጊ መረጃዎችን (ቲን፣ ንግድ ፈቃድ፣ ቼክ፣ ዋስ) በማስገባት ይመዝገቡ።\n"
        "2️⃣ **ማረጋገጥ (Approval)፦** ማመልከቻዎ በአድሚን ተመርምሮ ሲጸድቅ የአባልነት ደረጃዎ **Approved** ይሆናል።\n"
        "3️⃣ **ቁጠባና ብድር፦** እስከ 3 እጥፍ ብድር ማግኘት እና መክፈያ ቀኑን በካሌንደር ቆጣሪ መከታተል ይችላሉ።\n\n"
        "👇 **አገልግሎቱን ለመጀመር ከታች ያለውን አዝራር ይጫኑ፦**"
    )

    user_payload = json.dumps({"status": status, "savings": savings, "loan": loan, "daysLeft": days_left})
    encoded_payload = base64.b64encode(user_payload.encode()).decode()
    dynamic_url = f"{WEB_APP_URL}&tgWebAppStartParam={encoded_payload}" if "?" in WEB_APP_URL else f"{WEB_APP_URL}?tgWebAppStartParam={encoded_payload}"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 የመላ ሳኮ ፖርታል ይክፈቱ", web_app=WebAppInfo(url=dynamic_url))]
    ])
    
    await update.message.reply_text(welcome_text, reply_markup=keyboard, parse_mode="Markdown")

async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = json.loads(update.message.web_app_data.data)
        user = update.effective_user
        action = data.get("action")

        conn = sqlite3.connect('sacco_database.db')
        cursor = conn.cursor()

        if action == "register":
            cursor.execute('''
                INSERT OR REPLACE INTO users 
                (user_id, fullname, phone, tin, user_check, guarantor_name, guarantor_phone, guarantor_check, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user.id, data['fullName'], data['phone'], data['tin'], data.get('userCheck'),
                  data.get('guarantorName'), data.get('guarantorPhone'), data.get('guarantorCheck'), 'Pending'))
            conn.commit()

            await update.message.reply_text("⏳ **ማመልከቻዎ በስኬት ተልኳል!**\nአድሚኖች መርምረው አፕሩቭ እስኪያደርጉት ድረስ እባክዎ በትዕግስት ይጠብቁ።")

            admin_msg = (
                f"📥 **አዲስ የተመዘገበ አባል መረጃ!**\n\n"
                f"👤 **ስም:** {data['fullName']}\n"
                f"📞 **ስልክ:** `{data['phone']}`\n"
                f"🆔 **TIN:** `{data['tin']}`\n"
                f"💳 **የተበዳሪ ቼክ:** `{data.get('userCheck', '-')}`\n\n"
                f"🤝 **የዋስ ስም:** {data.get('guarantorName', '-')}\n"
                f"📞 **የዋስ ስልክ:** `{data.get('guarantorPhone', '-')}`\n"
                f"💳 **የዋስ ቼክ:** `{data.get('guarantorCheck', '-')}`\n"
                f"🆔 **Telegram ID:** `{user.id}`"
            )

            kbd = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Approve", callback_data=f"app_{user.id}"),
                 InlineKeyboardButton("❌ Reject", callback_data=f"rej_{user.id}"),
                 InlineKeyboardButton("🚫 Block", callback_data=f"blk_{user.id}")],
                [InlineKeyboardButton("💬 ከሰውየው ጋር በቀጥታ ተነጋገር", callback_data=f"chat_{user.id}")]
            ])

            if data.get('licenseImg'):
                img_data = base64.b64decode(data['licenseImg'].split(',')[1])
                await context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=BytesIO(img_data), caption=admin_msg, parse_mode="Markdown", reply_markup=kbd)
            else:
                await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_msg, parse_mode="Markdown", reply_markup=kbd)

        elif action == "update_account":
            target_id = int(data['targetUser'])
            days = int(data.get('days', 0))
            due_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d') if days > 0 else None

            cursor.execute('UPDATE users SET savings = savings + ?, loan_amount = ?, loan_due_date = ? WHERE user_id = ?',
                           (float(data.get('savings', 0)), float(data.get('loan', 0)), due_date, target_id))
            conn.commit()

            await update.message.reply_text(f"✅ **መረጃው ተዘምኗል!**\nተጠቃሚ ID: `{target_id}`", parse_mode="Markdown")
            await context.bot.send_message(chat_id=target_id, text=f"🔔 **አዲስ የሂሳብ ማሳወቂያ!**\n\nየብድርና ቁጠባ ሂሳብዎ በአድሚን ተዘምኗል። ቦቱን እንደገና `/start` በማለት ማየት ይችላሉ።")

        elif action == "add_admin":
            new_admin = int(data['newAdminId'])
            cursor.execute('INSERT OR IGNORE INTO admins (admin_id) VALUES (?)', (new_admin,))
            conn.commit()
            await update.message.reply_text(f"👑 ተጠቃሚ ID `{new_admin}` አድሚን ሆኖ ተሾሟል!")

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

    data_parts = query.data.split("_")
    action, target_id = data_parts[0], int(data_parts[1])

    conn = sqlite3.connect('sacco_database.db')
    cursor = conn.cursor()

    if action == "app":
        cursor.execute("UPDATE users SET status = 'Approved' WHERE user_id = ?", (target_id,))
        conn.commit()
        await query.edit_message_caption(caption=f"{query.message.caption}\n\n✅ **ሁኔታ፦ አባልነቱ ጽድቋል!**") if query.message.photo else await query.edit_message_text(text=f"{query.message.text}\n\n✅ **ሁኔታ፦ አባልነቱ ጽድቋል!**")
        await context.bot.send_message(chat_id=target_id, text="🎉 **እንኳን ደስ አለዎት!** የአባልነት ማመልከቻዎ ጸድቋል። ቦቱን እንደገና `/start` በማለት ዳሽቦርድዎን ማየት ይችላሉ።")

    elif action == "rej":
        cursor.execute("UPDATE users SET status = 'Rejected' WHERE user_id = ?", (target_id,))
        conn.commit()
        await context.bot.send_message(chat_id=target_id, text="⚠️ **ማሳሰቢያ፦** ማመልከቻዎ አልጸደቀም። እባክዎን ሰነዶችዎን አስተካክለው እንደገና ይላኩ።")

    elif action == "blk":
        cursor.execute("UPDATE users SET status = 'Blocked' WHERE user_id = ?", (target_id,))
        conn.commit()
        await context.bot.send_message(chat_id=target_id, text="🚫 **መለያዎ ታግዷል።**")

    elif action == "chat":
        await context.bot.send_message(chat_id=query.from_user.id, text=f"💬 ለተጠቃሚው `{target_id}` መልእክት ለመላክ ቦቱ ላይ መፃፍ ይችላሉ።", parse_mode="Markdown")

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
