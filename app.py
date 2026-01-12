from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import os
import asyncio

from app import app, process_flight_query

BOT_TOKEN = os.getenv("BOT_TOKEN")

telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

async def telegram_auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.message.from_user
        user_text = update.message.text

        reply = await process_flight_query(user_text, user_id=str(user.id))

        if isinstance(reply, list):
            for msg in reply:
                await update.message.reply_text(msg, parse_mode='Markdown')
        else:
            await update.message.reply_text(reply, parse_mode='Markdown')

    except Exception as e:
        print(f"Telegram Error: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع")

def main():
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, telegram_auto_reply))
   
   
    print("🤖 Telegram Worker Started")
    telegram_app.run_polling()

if __name__ == '__main__':
    with app.app_context():
        main()
