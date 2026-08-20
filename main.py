import os
import random
import asyncio
import threading
from flask import Flask, render_template, request, jsonify
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
import database as db

# BOT CONFIGURATION
BOT_TOKEN = "8543715567:AAFiBZK911QHVYC_UEq3pztxhyitTsU8g1M"
SUPER_ADMIN_ID = 5351353727

# ⚠️ ትኩረት: እዚች ጋር የ Render ድረ-ገጽህ አድራሻ አስገባ (ምሳሌ: https://mela-sacco-bot.onrender.com)
WEB_APP_URL = "https://mela-sacco-bot.onrender.com"  

app = Flask(__name__)
db.init_db(SUPER_ADMIN_ID)

# Telegram Bot Handler (ስለ SACCO ሙሉ መረጃ እና ሁለቱንም አማራጮች የያዘ)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # ስለ መላ SACCO በቂ መረጃ የሚሰጥ ጽሁፍ
    sacco_info = (
        "🏦 **እንኳን ወደ መላ SACCO በሰላም መጡ!**\n\n"
        "መላ SACCO የዲጂታል ብድር እና ቁጠባ ህብረት ስራ ማህበር ሲሆን የሚከተሉትን ዋና ዋና አገልግሎቶች ያቀርባል፡\n\n"
        "✨ **ዋና ዋና አገልግሎቶቻችን፡**\n"
        "• **የቁጠባ ሂሳብ (Savings):** በአስተማማኝ ሁኔታ ገንዘብዎን የሚቆጥቡበት እና የወለድ ጥቅም የሚያገኙበት።\n"
        "• **የብድር አገልግሎት (Loans):** ፈጣን እና ቀሊል የብድር አሰጣጥ ሂደት በዋስ እና በሰነድ ማረጋገጫ።\n"
        "• **ዲጂታል ዋሌት (Wallet):** የብድር፣ የቁጠባ እና የክፍያ ሁኔታዎን በቴሌግራም አፕ በቅጽበት የሚከታተሉበት።\n\n"
        "መመዝገብ እና አገልግሎቱን ማግኘት ለመጀመር ከታች ያለውን ቁልፍ ይጫኑ!"
    )

    # አዝራሮች (Buttons)
    keyboard = [
        [InlineKeyboardButton("📱 መላ SACCO Mini App ይክፈቱ", web_app=WebAppInfo(url=f"{WEB_APP_URL}/"))]
    ]

    # አንተ (Super Admin) ስትሆን የአድሚን ፓነል ቁልፍ ጨምሮ ያሳይሃል
    if user_id == SUPER_ADMIN_ID:
        keyboard.append([InlineKeyboardButton("🛡️ የአድሚን ፓነል ይክፈቱ (Admin)", web_app=WebAppInfo(url=f"{WEB_APP_URL}/admin"))])
        sacco_info += "\n\n👑 **ሰላም ዋና ስራ አስኪያጅ (GM)!** ሲስተሙን በሁለቱም መልኩ (እንደ ተጠቃሚ እና አድሚን) መሞከር ይችላሉ።"

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(sacco_info, reply_markup=reply_markup, parse_mode="Markdown")

# Flask Routes
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
    return jsonify({"status": "success", "reg_id": reg_id, "message": "ምዝገባው ተሳክቷል! አድሚን እስኪያጸድቅልዎ ድረስ በፔንዲንግ ይቆያሉ።"})

@app.route("/api/user/status/<int:telegram_id>", methods=["GET"])
def get_status(telegram_id):
    user = db.get_user(telegram_id)
    if user:
        return jsonify({"status": "success", "data": user})
    return jsonify({"status": "error", "message": "ተጠቃሚ አልተገኘም"}), 404

@app.route("/api/admin/approve", methods=["POST"])
def approve_user():
    data = request.json
    db.update_user_status(data['telegram_id'], data['status'])
    return jsonify({"status": "success", "message": f"የተጠቃሚው ሁኔታ ወደ {data['status']} ተቀይሯል።"})

@app.route("/api/admin/set-loan", methods=["POST"])
def set_loan():
    data = request.json
    db.update_loan(data['telegram_id'], data['amount'], data['interest'], data['days'])
    return jsonify({"status": "success", "message": "የብድር መረጃው ተስተካክሏል።"})

@app.route("/api/admin/request-otp", methods=["POST"])
def request_otp():
    data = request.json
    otp = str(random.randint(100000, 999999))
    db.save_otp(data['telegram_id'], otp)
    return jsonify({"status": "success", "message": "ጊዜያዊ OTP ወደ ዋናው አድሚን ተልኳል::", "otp": otp})

def start_bot():
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
