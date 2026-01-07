import os
import asyncio
from datetime import datetime
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# =====================
# Environment
# =====================
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN env variable not set!")

# =====================
# Flask + SQLite (Render Safe)
# =====================


if os.environ.get("RENDER") == "1":  # if running on Render
    db_path = "/tmp/flight_bot.db"
else:
    db_path = "instance/flight_bot.db"

SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# =====================
# Import Models & Flight System
# =====================
from models import db, init_db, add_initial_data, SearchHistory, City, Month, ArabicTextReplacement, Airline, Country
from nlp_engine import FlightNLP
from intent_analyzer import IntentAnalyzer
from flight_system import flight_system

# =====================
# Initialize DB
# =====================
init_db(app)
with app.app_context():
    db.create_all()
    add_initial_data()
    flight_system.init_app(app)

# =====================
# NLP & Intent
# =====================
nlp_engine = FlightNLP()
intent_analyzer = IntentAnalyzer()
with app.app_context():
    nlp_engine.init_app(app)

# =====================
# Telegram Bot
# =====================
telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

# =====================
# Helper: Log Search History
# =====================
def log_search_history(user_id, text, nlp_result, flights_found):
    try:
        with app.app_context():
            search = SearchHistory(
                user_id=user_id,
                query_text=text,
                success=True,
                flights_found=flights_found
            )
            if nlp_result.get("query"):
                q = nlp_result["query"]
                search.origin = q.get("origin")
                search.destination = q.get("destination")
                search.flight_date = datetime.strptime(q["date"], "%Y-%m-%d").date()
                search.passengers = q.get("adults", 1)
            search.set_nlp_result(nlp_result)
            db.session.add(search)
            db.session.commit()
    except Exception as e:
        print(f"❌ Failed to log search: {e}")

# =====================
# Core Flight Processing
# =====================
async def process_flight_query(text, user_id):
    try:
        intent = intent_analyzer.analyze_intent(text)
        if intent["intent"] in ["greeting", "thanks", "help", "general_question", "gibberish"]:
            return intent["response"]

        nlp_result = nlp_engine.process_query(text)
        if not nlp_result.get("success"):
            return "✈️ لم أفهم تفاصيل الرحلة. مثال:\nرحلة من الرياض إلى دبي يوم 15 ديسمبر"

        query = nlp_result["query"]

        with app.app_context():
            search_result = flight_system.search_flights_safe(
                query["origin"],
                query["destination"],
                query["date"],
                query.get("adults", 1)
            )

            formatted_results = flight_system.format_flight_results(search_result)
            messages = flight_system.get_flight_response_messages(query, formatted_results)

            log_search_history(
                user_id,
                text,
                nlp_result,
                formatted_results.get("count", 0)
            )

            return messages
    except Exception as e:
        print(f"❌ Error processing query: {e}")
        return "❌ حدث خطأ أثناء معالجة طلبك. يرجى المحاولة مرة أخرى."

# =====================
# Telegram Handlers
# =====================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text
    print(f"📩 Message from {user.first_name}: {text}")

    reply = await process_flight_query(text, str(user.id))

    if isinstance(reply, list):
        for msg in reply:
            await update.message.reply_text(msg, parse_mode="Markdown")
    else:
        await update.message.reply_text(reply, parse_mode="Markdown")

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📎 لا أستطيع معالجة الصور أو الملفات الآن.\n✍️ أرسل طلب الرحلة نصيًا."
    )

telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
telegram_app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_media))

# =====================
# Run Telegram Polling (blocking mode - أكثر استقرارًا على Render)
# =====================
if __name__ == "__main__":
    print("🤖 Telegram Bot Started (Polling)")
    telegram_app.run_polling()
