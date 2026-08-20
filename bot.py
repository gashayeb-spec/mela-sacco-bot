import json
import logging
import os
import sqlite3
import base64
from io import BytesIO
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
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://gashayeb-spec.github.io/mela-sacco-bot/?v=8")

def init_db():
    conn = sqlite3.connect('sacco_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            fullname TEXT,
            phone TEXT,
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 የመላ ሳኮ ፖርታል ይክፈቱ", web_app=WebAppInfo(url=WEB_APP_URL))]
    ])
    await update.message.reply_text("🏥 **እንኳን ወደ መላ ህብረት ስራ ማህበር (Mela SACCO) በደህና መጡ!**\n\nከታች ያለውን አዝራር በመጫን ስለ ድርጅቱ ማወቅ፣ መመዝገብ ወይም የዋስትና ሰነድ ማያያዝ ይችላሉ።", reply_markup=keyboard, parse_mode="Markdown")

async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = json.loads(update.message.web_app_data.data)
        user = update.effective_user
        action = data.get("action")

        conn = sqlite3.connect('sacco_database.db')
        cursor = conn.cursor()

        # 1. የአባልነት ምዝገባ መረጃ መቀበያ
        if action == "register":
            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, fullname, phone, tin, vat, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user.id, data['fullName'], data['phone'], data['tin'], data.get('vat', '-'), 'Pending'))
            conn.commit()

            await update.message.reply_text(f"⏳ **የአባልነት ማመልከቻዎ ተልኳል!**\n\nየእርስዎ የመዝገብ ቁጥር (Member ID)፦ `{user.id}` ነው\nአድሚኑ መርምሮ እስኪያጸድቅልዎ ድረስ ይቆዩ።", parse_mode="Markdown")

            admin_msg = (
                f"📥 **አዲስ የአባልነት ማመልከቻ!**\n\n"
                f"👤 **ስም:** {data['fullName']}\n"
                f"📞 **ስልክ:** `{data['phone']}`\n"
                f"🆔 **TIN:** `{data['tin']}`\n"
                f"📄 **VAT:** `{data.get('vat', '-')}`\n"
                f"🔢 **የመዝገብ ቁጥር (ID):** `{user.id}`"
            )

            kbd = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Approve", callback_data=f"app_{user.id}"),
                 InlineKeyboardButton("❌ Reject", callback_data=f"rej_{user.id}")]
            ])

            if data.get('licenseImg'):
                img_data = base64.b64decode(data['licenseImg'].split(',')[1])
                await context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=BytesIO(img_data), caption=admin_msg, parse_mode="Markdown", reply_markup=kbd)
            else:
                await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_msg, parse_mode="Markdown", reply_markup=kbd)

        # 2. የዋስትና ሰነድ መቀበያ
        elif action == "submit_guarantor":
            member_id = int(data['memberId'])
            cursor.execute('''
                UPDATE users SET user_check=?, guarantor_name=?, guarantor_phone=?, guarantor_check=?
                WHERE user_id=?
            ''', (data['userCheck'], data['guarantorName'], data['guarantorPhone'], data['guarantorCheck'], member_id))
            conn.commit()

            await update.message.reply_text("✅ **የዋስትና ሰነድዎ በስኬት ተልኳል!**")

            guar_msg = (
                f"🤝 **አዲስ የዋስትና ሰነድ ደርሷል!**\n\n"
                f"🔢 **የአባሉ ID:** `{member_id}`\n"
                f"💳 **የተበዳሪው ቼክ No:** `{data['userCheck']}`\n"
                f"👤 **የዋስ ስም:** {data['guarantorName']}\n"
                f"📞 **የዋስ ስልክ:** `{data['guarantorPhone']}`\n"
                f"💳 **የዋስ ቼክ No:** `{data['guarantorCheck']}`"
            )
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=guar_msg, parse_mode="Markdown")

        # 3. የአድሚን አካውንት ማስተካከያ
        elif action == "update_account":
            target_id = int(data['targetUser'])
            cursor.execute('UPDATE users SET savings = savings + ?, loan_amount = ? WHERE user_id = ?',
                           (float(data.get('savings', 0)), float(data.get('loan', 0)), target_id))
            conn.commit()
            await update.message.reply_text(f"✅ የመዝገብ ቁጥር `{target_id}` መረጃ ተዘምኗል!")

        # 4. ብሮድካስት
        elif action == "broadcast":
            msg_text = data['message']
            cursor.execute("SELECT user_id FROM users")
            all_users = cursor.fetchall()
            for u in all_users:
                try: await context.bot.send_message(chat_id=u[0], text=f"📢 **የመላ ሳኮ ማስታወቂያ፦**\n\n{msg_text}", parse_mode="Markdown")
                except: pass
            await update.message.reply_text("📢 ማስታወቂያው ተልኳል!")

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
        await query.message.reply_text(f"✅ የመዝገብ ቁጥር `{target_id}` አባልነቱ ጸድቋል!")
        await context.bot.send_message(chat_id=target_id, text="🎉 **እንኳን ደስ አለዎት!** የአባልነት ማመልከቻዎ ጸድቋል። አሁን ብድር መጠየቅና የዋስትና ሰነድ ማያያዝ ይችላሉ።")

    elif action == "rej":
        cursor.execute("UPDATE users SET status = 'Rejected' WHERE user_id = ?", (target_id,))
        conn.commit()
        await context.bot.send_message(chat_id=target_id, text="⚠️ **ማሳሰቢያ፦** ማመልከቻዎ አልጸደቀም። እባክዎን ሰነዶችዎን አስተካክለው እንደገና ይላኩ።")

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
