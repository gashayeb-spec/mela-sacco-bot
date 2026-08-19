import json
import logging
import os
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN", "8543715567:AAG6rHF_4D8RjuZJLsYqwzRRjhBjXjAbNHM")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "5351353727"))
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://your-github-username.github.io/mela-sacco-bot/")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("መላ ሳኮ Mini App ክፈት 🚀", web_app_url=WebAppInfo(url=WEB_APP_URL))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "እንኳን ወደ **መላ ሳኮ (Mela SACCO)** በደህና መጡ!\n\nታች ያለውን በተን በመጫን አገልግሎታችንን ያግኙ፡",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        raw_data = update.message.web_app_data.data
        data = json.loads(raw_data)
        
        full_name = data.get("fullName", "ያልተጠቀሰ")
        phone = data.get("phone", "ያልተጠቀሰ")
        message = data.get("message", "ያልተጠቀሰ")
        language = data.get("language", "am")
        
        user = update.effective_user
        
        confirm_text = (
            "✅ **መልእክትዎ በስኬት ደርሶናል!**\nበቅርቡ እናገኝዎታለን።" 
            if language == 'am' 
            else "✅ **Message received successfully!**\nWe will contact you soon."
        )
        await update.message.reply_text(confirm_text, parse_mode="Markdown")
        
        admin_notification = (
            "📥 **አዲስ የቅጽ ምዝገባ ከ Mini App!**\n\n"
            f"👤 **ስም:** {full_name}\n"
            f"📞 **ስልክ:** {phone}\n"
            f"💬 **መልእክት:** {message}\n"
            f"🌐 **ቋንቋ:** {language}\n\n"
            f"🔗 **የላኪው Telegram:** @{user.username if user.username else 'የለውም'} (ID: `{user.id}`)"
        )
        
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID, 
            text=admin_notification, 
            parse_mode="Markdown"
        )

    except Exception as e:
        logging.error(f"Error processing WebApp data: {e}")
        await update.message.reply_text("የተሳሳተ መረጃ ተልኳል። እባክዎ እንደገና ይሞክሩ።")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))

    print("🤖 Mela SACCO Bot እየሰራ ነው...")
    app.run_polling()

if __name__ == "__main__":
    main()
