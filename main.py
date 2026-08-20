import os
import random
import asyncio
import threading
from flask import Flask, render_template, request, jsonify
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
import database as db

# ==================== CONFIGURATION ====================
BOT_TOKEN = "8543715567:AAFiBZK911QHVYC_UEq3pztxhyitTsU8g1M"
SUPER_ADMIN_ID = 5351353727

# ⚠️ የ Render URL ህን እዚህ ጋር ያረጋግጡ
WEB_APP_URL = "https://mela-sacco-bot.onrender.com"  

# ⚠️ የቴሌግራም ቻናልህ ID ወይም Username (ቦቱን በቻናሉ Admin ማድረግህን እንዳትረሳ)
CHANNEL_ID = "@mela_sacco_channel" 

app = Flask(__name__)
db.init_db(SUPER_ADMIN_ID)

telegram_app = None

# ==================== BOT HANDLERS ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    sacco_info = (
        "🏦 **እንኳን ወደ መላ SACCO በሰላም መጡ!**\n\n"
        "መላ SACCO የዲጂታል ብድር እና ቁጠባ ህብረት ስራ ማህበር ሲሆን የሚከተሉትን አገልግሎቶች ያቀርባል፡\n\n"
        "• **የቁጠባ ሂሳብ (Savings):** በአስተማማኝ ሁኔታ ገንዘብዎን የሚቆጥቡበት\n"
        "• **የብድር አገልግሎት (Loans):** ፈጣን የብድር አሰጣጥ እና የሰነድ ማረጋገጫ\n"
        "• **ዲጂታል ዋሌት (Wallet):** የብድር፣ የቁጠባ እና የክፍያ ሁኔታዎን የሚከታተሉበት\n\n"
        "አገልግሎቱን ለማግኘት ከታች ያለውን ቁልፍ ይጫኑ!"
    )

    keyboard = [
        [InlineKeyboardButton("📱 መላ SACCO Mini App", web_app=WebAppInfo(url=f"{WEB_APP_URL}/"))]
    ]

    if user_id == SUPER_ADMIN_ID or db.is_admin(user_id):
        keyboard.append([InlineKeyboardButton("🛡️ የአድሚን ፓነል (Admin Panel)", web_app=WebAppInfo(url=f"{WEB_APP_URL}/admin"))])
        sacco_info += "\n\n👑 **የአድሚን ስልጣን አለዎት!**"

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(sacco_info, reply_markup=reply_markup, parse_mode="Markdown")

def send_telegram_msg_async(chat_id, text):
    if telegram_app and telegram_app.bot:
        asyncio.run_coroutine_threadsafe(
            telegram_app.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown"),
            telegram_app.loop
        )

# ==================== FLASK API ROUTES ====================
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
        f"📄 **TIN:** {data.get('tin', 'የለውም')}\n"
        f"🏬 **ንግድ ፈቃድ:** {data.get('trade_lic', 'የለውም')}\n"
        f"🧾 **VAT:** {data.get('vat_no', 'የለውም')}\n\n"
        f"እባክዎን በአድሚን ፓነል ገብተው ሰነዶቹን ያጽድቁ።"
    )
    send_telegram_msg_async(SUPER_ADMIN_ID, admin_msg)

    channel_msg = (
        f"🎉 **አዲስ አባል ተመዝግቧል!**\n\n"
        f"አባል **{data.get('full_name')}** بالمላ SACCO ዲጂታል ሲስተም ላይ በስኬት ተመዝግበዋል።"
    )
    send_telegram_msg_async(CHANNEL_ID, channel_msg)

    return jsonify({"status": "success", "reg_id": reg_id, "message": "ምዝገባው ተሳክቷል! አድሚን እስኪያጸድቅልዎ ድረስ በፔንዲንግ ይቆያሉ።"})

@app.route("/api/admin/approve", methods=["POST"])
def approve_user():
    data = request.json
    db.update_user_status(data['telegram_id'], data['status'])
    
    status_str = "ጽድቋል ✅" if data['status'] == 'Approved' else "ተሰርዟል ❌"
    user_msg = f"🔔 **የአባልነት ማረጋገጫ መረጃ**\n\nየመላ SACCO አባልነት ማመልከቻዎ **{status_str}**።"
    send_telegram_msg_async(data['telegram_id'], user_msg)

    return jsonify({"status": "success", "message": f"የተጠቃሚው ሁኔታ ወደ {data['status']} ተቀይሯል።"})

@app.route("/api/admin/set-loan", methods=["POST"])
def set_loan():
    data = request.json
    db.update_loan(data['telegram_id'], data['amount'], data['interest'], data['days'])
    
    loan_msg = (
        f"🎉 **የብድር ፈቃድ ማስታወቂያ!**\n\n"
        f"💵 **የተፈቀደ ብድር:** {data['amount']} ETB\n"
        f"📈 **ወለድ:** {data['interest']}%\n"
        f"⏳ **የመክፈያ ጊዜ:** {data['days']} ቀናት\n\n"
        f"ዝርዝሩን በሚኒ አፕ ዋሌትዎ ላይ ማየት ይችላሉ።"
    )
    send_telegram_msg_async(data['telegram_id'], loan_msg)

    return jsonify({"status": "success", "message": "የብድር መረጃው ተስተካክሏል።"})

@app.route("/api/admin/send-message", methods=["POST"])
def send_message():
    data = request.json
    target_type = data.get('target_type')
    msg_text = data.get('message')
    
    if target_type == 'single':
        target_id = data.get('target_id')
        send_telegram_msg_async(target_id, f"💬 **ከአድሚን የተላከ መልእክት:**\n\n{msg_text}")
    elif target_type == 'all':
        users = db.get_all_users()
        for u in users:
            send_telegram_msg_async(u['telegram_id'], f"📢 **አጠቃላይ ማስታወቂያ:**\n\n{msg_text}")
    elif target_type == 'channel':
        send_telegram_msg_async(CHANNEL_ID, f"📢 **የመላ SACCO ኦፊሴላዊ ማስታወቂያ:**\n\n{msg_text}")

    return jsonify({"status": "success", "message": "መልእክቱ በተሳካ ሁኔታ ተልኳል!"})

@app.route("/api/admin/get-pending-users", methods=["GET"])
def pending_users():
    users = db.get_pending_users()
    return jsonify({"status": "success", "users": users})

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
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
