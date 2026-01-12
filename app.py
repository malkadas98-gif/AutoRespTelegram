import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters
)

from dotenv import load_dotenv

load_dotenv()
from core_logic import process_flight_query  # منطق فقط، بدون Flask

# =============================
# Logging
# =============================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# =============================
# Token
# =============================
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("❌ TELEGRAM_BOT_TOKEN is missing")

# =============================
# Handlers
# =============================
async def telegram_auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message or not update.message.text:
            return

        user = update.message.from_user
        text = update.message.text

        logger.info(f"📩 Message from {user.first_name}: {text}")

        reply = await process_flight_query(text, user_id=str(user.id))

        if isinstance(reply, list):
            for msg in reply:
                await update.message.reply_text(msg, parse_mode="Markdown")
        else:
            await update.message.reply_text(reply, parse_mode="Markdown")

    except Exception as e:
        logger.exception("❌ Telegram handler error")
        await update.message.reply_text("❌ حدث خطأ غير متوقع، حاول مرة أخرى")

# =============================
# Main
# =============================
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, telegram_auto_reply)
    )

    logger.info("🤖 Telegram Bot started (Background Worker)")
    logger.info("✅ Polling mode active")

    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=["message"],
        close_loop=False
    )

if __name__ == "__main__":
    main()
