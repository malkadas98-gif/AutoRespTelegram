import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

from app import process_flight_query  # تستخدم نفس المنطق

BOT_TOKEN = os.environ["BOT_TOKEN"]  # هنا يجب أن يكون موجود

telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

async def telegram_auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text

    reply = await process_flight_query(text, user_id=str(user.id))

    if isinstance(reply, list):
        for msg in reply:
            await update.message.reply_text(msg, parse_mode="Markdown")
    else:
        await update.message.reply_text(reply, parse_mode="Markdown")

telegram_app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, telegram_auto_reply)
)

if __name__ == "__main__":
    print("🤖 Telegram Bot Worker Started")
    telegram_app.run_polling()
