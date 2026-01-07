import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# =====================
# Environment
# =====================
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN env variable not set!")

# =====================
# Handlers
# =====================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text
    print(f"📩 Message from {user.first_name}: {text}")
    await update.message.reply_text(f"مرحباً {user.first_name}! تلقيت رسالتك: {text}")

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📎 لا أستطيع معالجة الصور أو الملفات الآن. أرسل رسالة نصية.")

# =====================
# Telegram App
# =====================
telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
telegram_app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_media))

# =====================
# Main Polling Loop
# =====================
if __name__ == "__main__":
    print("🤖 Telegram Bot Starting Polling...")
    # Run polling in blocking mode (هذا أكثر استقراراً على Render)
    telegram_app.run_polling()
