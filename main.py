import os
import random
from flask import Flask, render_template, request, jsonify
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
import database as db

# የተላኩት መረጃዎች እዚህ ጋር ገብተዋል
BOT_TOKEN = "8543715567:AAFiBZK911QHVYC_UEq3pztxhyitTsU8g1M"
SUPER_ADMIN_ID = 5351353727
WEB_APP_URL = "https://your-domain.com"  # አፕሊኬሽኑን የምትጭንበት የHTTPS domain address

app = Flask(__name__)
db.init_db(SUPER_ADMIN_ID)

# Telegram Bot Handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyboard = [
        [InlineKeyboardButton("መላ SACCO Mini App ይክፈቱ 🏦", web_app=WebAppInfo(url=WEB_APP_URL))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_msg = "እንኳን ወደ **መላ SACCO** በሰላም መጡ! አገልግሎቱን ለማግኘት ከታች ያለውን ቁልፍ ይጫኑ።"
    if user_id == SUPER_ADMIN_ID:
        welcome_msg += "\n\nስማችሁ እንደ **ዋና ስራ አስኪያጅ (GM)** በሲስተሙ ተመዝግቧል።"

    await update.message.reply_text(
        welcome_msg,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# Backend API Routes
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

if __name__ == "__main__":
    import threading
    def run_bot():
        telegram_app = Application.builder().token(BOT_TOKEN).build()
        telegram_app.add_handler(CommandHandler("start", start))
        telegram_app.run_polling()

    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, debug=True)
