import os
import asyncio
from datetime import datetime

from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    ContextTypes
)

from models import (
    db, SearchHistory, init_db, add_initial_data,
    City, Month, ArabicTextReplacement, Airline, Country
)

from nlp_engine import FlightNLP
from intent_analyzer import IntentAnalyzer
from flight_system import flight_system

# ===============================
# Environment
# ===============================
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # https://your-app.onrender.com
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///flight_bot.db")

# ===============================
# Flask App
# ===============================
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ===============================
# Database
# ===============================
init_db(app)

with app.app_context():
    db.create_all()
    add_initial_data()

# ===============================
# NLP & Intent
# ===============================
nlp_engine = FlightNLP()
intent_analyzer = IntentAnalyzer()

# ===============================
# Telegram App
# ===============================
telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

# ===============================
# Helpers
# ===============================
def log_search_history(user_id, text, nlp_result, success, flights_found=0):
    try:
        with app.app_context():
            search = SearchHistory(
                user_id=user_id,
                query_text=text,
                success=success,
                flights_found=flights_found
            )

            if nlp_result.get("query"):
                q = nlp_result["query"]
                search.origin = q.get("origin")
                search.destination = q.get("destination")
                search.flight_date = datetime.strptime(
                    q["date"], "%Y-%m-%d"
                ).date()
                search.passengers = q.get("adults", 1)

            search.set_nlp_result(nlp_result)
            db.session.add(search)
            db.session.commit()
    except Exception as e:
        print(f"❌ Log failed: {e}")

# ===============================
# Core Logic
# ===============================
async def process_flight_query(text, user_id=None):
    intent = intent_analyzer.analyze_intent(text)

    if intent["intent"] in [
        "greeting", "thanks", "help",
        "general_question", "gibberish", "unclear"
    ]:
        return intent["response"]

    nlp_result = nlp_engine.process_query(text)

    should_call = intent_analyzer.should_use_amadeus(intent, nlp_result)

    if should_call and nlp_result.get("success"):
        q = nlp_result["query"]

        with app.app_context():
            result = flight_system.search_flights_safe(
                q["origin"],
                q["destination"],
                q["date"],
                q["adults"]
            )

            formatted = flight_system.format_flight_results(result)
            messages = flight_system.get_flight_response_messages(
                q, formatted
            )

            if user_id:
                log_search_history(
                    user_id,
                    text,
                    nlp_result,
                    True,
                    formatted.get("count", 0)
                )

            return messages

    return (
        "✈️ اكتب طلبك بهذا الشكل:\n\n"
        "رحلة من الرياض إلى دبي يوم 20 ديسمبر"
    )

# ===============================
# Telegram Handlers
# ===============================
async def telegram_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text

    response = await process_flight_query(text, str(user.id))

    if isinstance(response, list):
        for msg in response:
            await update.message.reply_text(msg, parse_mode="Markdown")
    else:
        await update.message.reply_text(response, parse_mode="Markdown")

async def telegram_media_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📎 حالياً لا يمكن معالجة الصور أو الملفات.\n"
        "✍️ اكتب تفاصيل رحلتك نصياً."
    )

telegram_app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, telegram_text_handler)
)
telegram_app.add_handler(
    MessageHandler(filters.PHOTO | filters.Document.ALL, telegram_media_handler)
)

# ===============================
# Webhook Route
# ===============================
@app.route("/telegram-webhook", methods=["POST"])
def telegram_webhook():
    update = Update.de_json(request.get_json(), telegram_app.bot)
    asyncio.run(telegram_app.process_update(update))
    return "OK"

# ===============================
# Health Check
# ===============================
@app.route("/health")
def health():
    return jsonify({"status": "ok"})

# ===============================
# Startup
# ===============================
if __name__ == "__main__":
    print("🚀 Starting Telegram Webhook Bot")

    with app.app_context():
        flight_system.init_app(app)
        nlp_engine.init_app(app)

    # Set webhook
    asyncio.run(
        telegram_app.bot.set_webhook(
            url=f"{WEBHOOK_URL}/telegram-webhook"
        )
    )

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
