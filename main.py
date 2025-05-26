import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI
import time

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Env
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Anti-spam settings
user_last_message_time = {}
group_last_response_time = 0
last_messages = {}

# OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 สวัสดี! ฉันคือ Echo แห่ง Shibora ถามมาได้เลย")

# Handle messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global group_last_response_time

    user_id = update.effective_user.id
    text = update.message.text.strip()
    current_time = time.time()

    # Per-user rate limit
    if user_id in user_last_message_time and current_time - user_last_message_time[user_id] < 10:
        return
    user_last_message_time[user_id] = current_time

    # Group-wide cooldown
    if current_time - group_last_response_time < 5:
        return
    group_last_response_time = current_time

    # Avoid repeated messages
    if last_messages.get(user_id) == text:
        return
    last_messages[user_id] = text

    # Generate reply
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": text}]
        )
        reply = response.choices[0].message.content.strip()
        await update.message.reply_text(reply)

    except Exception as e:
        logger.error(f"OpenAI Error: {e}")
        await update.message.reply_text("⚠️ ขอโทษ ระบบขัดข้อง ลองใหม่อีกครั้งครับ")

# Main entry
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Echo is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
