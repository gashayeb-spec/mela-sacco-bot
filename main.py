import os
import random
import asyncio
import threading
from flask import Flask, render_template, request, jsonify
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
import database as db

BOT_TOKEN = "8543715567:AAFiBZK911QHVYC_UEq3pztxhyitTsU8g1M"
SUPER_ADMIN_ID = 5351353727
WEB_APP_URL = "https://mela-sacco-bot.onrender.com"  
CHANNEL_ID = "@mela_sacco_channel" 

app = Flask(__name__)
db.init_db(SUPER_ADMIN_ID)
telegram_app = None

# Async Helper for Telegram Messages
def send_telegram_msg_async(chat_id, text):
    if telegram_app and telegram_app.bot:
        asyncio.run_coroutine_threadsafe(
            telegram_app.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown"),
            telegram_app.loop
        )

# ==================== API ROUTES ====================

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/admin")
def admin():
    return render_template("admin.html")

# 1. አዲስ ምዝገባ - ወደ ዳታቤዝ ይገባል + ለዋና አድሚን እና ለቻናል ይላካል
@app.route("/api/register", methods=["POST"])
def register():
    data = request.json
    reg_id = db.register_user(data)
    
    admin_msg = (
        f"📥 **አዲስ የምዝገባ ጥያቄ ደርሷል!**\n\n"
        f"👤 **ስም:** {data.get('full_name')}\n"
        f"🆔 **መዝገብ ID:** `{reg_id}`\n"
        f"📞 **ስልክ:** {data.get('phone')}\n"
        f"📄 **TIN:** {data.get('tin', 'የለውም')}\n\n"
        f"በአድሚን ፓነል ገብተው ማረጋገጥ ይችላሉ።"
    )
    send_telegram_msg_async(SUPER_ADMIN_ID, admin_msg)
    return jsonify({"status": "success", "reg_id": reg_id, "message": "ምዝገባው ተሳክቷል!"})

# 2. የአድሚን ፓነል በየሰከንዱ አዳዲስ ተመዝጋቢዎችን የሚቀበልበት (Live Polling)
@app.route("/api/admin/get-all-users", methods=["GET"])
def get_all_users():
    users = db.get_all_users()
    return jsonify({"status": "success", "users": users})

# 3. አድሚን አፕሩቭ ሲያደርግ - ለተጠቃሚው በቴሌግራም ይደርሳል
@app.route("/api/admin/approve", methods=["POST"])
def approve_user():
    data = request.json
    db.update_user_status(data['telegram_id'], data['status'])
    
    status_str = "ጽድቋል ✅" if data['status'] == 'Approved' else "ተሰርዟል ❌"
    user_msg = f"🔔 **የመላ SACCO አባልነት ማረጋገጫ**\n\nየአባልነት ማመልከቻዎ **{status_str}**።"
    send_telegram_msg_async(data['telegram_id'], user_msg)

    return jsonify({"status": "success", "message": f"ሁኔታው ወደ {data['status']} ተቀይሯል።"})

# 4. የአድሚኖች የውስጥ መልእክት ልውውጥ (Admin-to-Admin & Admin-to-User)
@app.route("/api/admin/send-internal-msg", methods=["POST"])
def send_internal_msg():
    data = request.json
    sender_role = data.get('sender_role')
    target_id = data.get('target_id')
    message_text = data.get('message')
    
    # መልእክቱን ዳታቤዝ ላይ መመዝገብ
    db.save_admin_message(sender_role, target_id, message_text)
    
    # ለተቀባዩ በቴሌግራም ማሳወቅ
    notification = f"📩 **ከ[{sender_role}] የተላከ አዲስ መልእክት:**\n\n{message_text}"
    send_telegram_msg_async(target_id, notification)
    
    return jsonify({"status": "success", "message": "መልእክቱ ደርሷል!"})

# 5. የአድሚን የቻት ሂስቶሪ ማምጫ
@app.route("/api/admin/get-messages/<int:target_id>", methods=["GET"])
def get_messages(target_id):
    messages = db.get_admin_messages(target_id)
    return jsonify({"status": "success", "messages": messages})

# ==================== BOT START ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyboard = [[InlineKeyboardButton("📱 መላ SACCO Mini App", web_app=WebAppInfo(url=f"{WEB_APP_URL}/"))]]
    if user_id == SUPER_ADMIN_ID or db.is_admin(user_id):
        keyboard.append([InlineKeyboardButton("🛡️ የአድሚን ፓነል", web_app=WebAppInfo(url=f"{WEB_APP_URL}/admin"))])
    
    await update.message.reply_text("🏦 **እንኳን ወደ መላ SACCO በሰላም መጡ!**", reply_markup=InlineKeyboardMarkup(keyboard))

def start_bot():
    global telegram_app
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    telegram_app = Application.builder().token(BOT_TOKEN).build()
    telegram_app.add_handler(CommandHandler("start", start))
    loop.run_until_complete(telegram_app.initialize())
    loop.run_until_complete(telegram_app.start())
    loop.run_until_complete(telegram_app.updater.start_polling())
    loop.run_forever()

if __name__ == "__main__":
    threading.Thread(target=start_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
