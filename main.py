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

app = Flask(__name__)
db.init_db(SUPER_ADMIN_ID)
telegram_app = None

def send_telegram_msg_async(chat_id, text):
    if telegram_app and telegram_app.bot:
        asyncio.run_coroutine_threadsafe(
            telegram_app.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown"),
            telegram_app.loop
        )

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/admin")
def admin():
    return render_template("admin.html")

@app.route("/api/register", methods=["POST"])
def register():
    data = request.json
    reg_id = db.register_user(data)
    
    admin_msg = (
        f"📥 **አዲስ የምዝገባ ጥያቄ ደርሷል!**\n\n"
        f"👤 **ስም:** {data.get('full_name')}\n"
        f"🆔 **መዝገብ ID:** `{reg_id}`\n"
        f"📞 **ስልክ:** {data.get('phone')}\n"
    )
    send_telegram_msg_async(SUPER_ADMIN_ID, admin_msg)
    return jsonify({"status": "success", "reg_id": reg_id, "message": "ምዝገባው ተሳክቷል!"})

@app.route("/api/admin/get-all-users", methods=["GET"])
def get_all_users():
    users = db.get_all_users()
    return jsonify({"status": "success", "users": users})

# የተወሰነ ተጠቃሚ ደብተር ዝርዝር ማምጫ API
@app.route("/api/admin/get-user/<int:telegram_id>", methods=["GET"])
def get_user_details(telegram_id):
    user = db.get_user_by_tg_id(telegram_id)
    return jsonify({"status": "success", "user": user})

@app.route("/api/admin/approve", methods=["POST"])
def approve_user():
    data = request.json
    db.update_user_status(data['telegram_id'], data['status'])
    
    status_str = "ጽድቋል ✅" if data['status'] == 'Approved' else "ተሰርዟል ❌"
    user_msg = f"🔔 **የመላ SACCO አባልነት ማረጋገጫ**\n\nየአባልነት ማመልከቻዎ **{status_str}**።"
    send_telegram_msg_async(data['telegram_id'], user_msg)

    return jsonify({"status": "success", "message": f"ሁኔታው ወደ {data['status']} ተቀይሯል።"})

# የአባልን ደብተር (አክሲዮን፣ ብድር፣ ቁጠባ) ማስተካከያ API
@app.route("/api/admin/update-ledger", methods=["POST"])
def update_ledger():
    data = request.json
    db.update_member_ledger(data)
    
    notify_msg = (
        f"📊 **የአባልነት ደብተርዎ ተሻሽሏል!**\n\n"
        f"🎟️ **የተገዛ አክሲዮን:** {data['shares_bought']} አክሲዮን ({data['share_amount']} ETB)\n"
        f"💰 **የቁጠባ መጠን:** {data['savings']} ETB\n"
        f"💳 **የተፈቀደ ብድር:** {data['loan_amount']} ETB (ወለድ: {data['loan_interest']}%, የመክፈያ ጊዜ: {data['loan_days']} ቀን)"
    )
    send_telegram_msg_async(data['telegram_id'], notify_msg)
    
    return jsonify({"status": "success", "message": "የአባሉ ደብተር በስኬት ተዘምኗል!"})

@app.route("/api/admin/send-internal-msg", methods=["POST"])
def send_internal_msg():
    data = request.json
    db.save_admin_message(data.get('sender_role'), data.get('target_id'), data.get('message'))
    notification = f"📩 **ከ[{data.get('sender_role')}] የተላከ አዲስ መልእክት:**\n\n{data.get('message')}"
    send_telegram_msg_async(data.get('target_id'), notification)
    return jsonify({"status": "success", "message": "መልእክቱ ደርሷል!"})

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📱 መላ SACCO Mini App", web_app=WebAppInfo(url=f"{WEB_APP_URL}/"))]]
    if update.effective_user.id == SUPER_ADMIN_ID or db.is_admin(update.effective_user.id):
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
