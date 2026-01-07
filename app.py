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
# Telegram Handlers
# =====================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text
    print(f"📩 رسالة من {user.first_name}: {text}")

    # الرد مباشرة
    reply = f"مرحباً {user.first_name}! تلقيت رسالتك: {text}"
    await update.message.reply_text(reply)

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📎 لا أستطيع معالجة الصور أو الملفات الآن.\n✍️ أرسل رسالة نصية."
    )

# =====================
# Telegram App
# =====================
telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
telegram_app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_media))

# =====================
# Main
# =====================
async def main():
    print("🤖 Telegram Bot Started (Polling)")
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.bot.initialize()
    await telegram_app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
