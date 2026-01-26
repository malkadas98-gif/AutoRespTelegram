# app.py
import os
import logging
import requests
import asyncio
from flask import Flask, request
from datetime import datetime

from models import (
    db, SearchHistory, SystemSettings, APIUsage,
    init_db, add_initial_data,
    City, Month, ArabicTextReplacement, Airline, Country
)
from nlp_engine import FlightNLP
from flight_system import flight_system
from intent_analyzer import IntentAnalyzer

# ================== Logging ==================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ================== Flask ==================
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-key")

basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    "sqlite:///" + os.path.join(basedir, "flight_bot.db")
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

init_db(app)

# ================== NLP & Intent ==================
nlp_engine = FlightNLP()
intent_analyzer = IntentAnalyzer()

# ================== WhatsApp Config ==================
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

# ================== Database Setup ==================
def setup_database():
    with app.app_context():
        db.create_all()
        add_initial_data()
        logger.info("✅ Database initialized")

# ================== WhatsApp Send ==================
def send_whatsapp_message(to, text):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": text}
    }
    r = requests.post(url, headers=headers, json=payload)
    logger.info(f"📤 WhatsApp sent: {r.status_code}")

# ================== Search History ==================
def log_search_history(user_id, query_text, nlp_result, success, flights_found=0):
    try:
        with app.app_context():
            search = SearchHistory(
                user_id=user_id,
                query_text=query_text,
                success=success,
                flights_found=flights_found
            )

            if nlp_result.get("query"):
                q = nlp_result["query"]
                search.origin = q["origin"]
                search.destination = q["destination"]
                search.flight_date = datetime.strptime(q["date"], "%Y-%m-%d").date()
                search.passengers = q["adults"]

            search.set_nlp_result(nlp_result)
            db.session.add(search)
            db.session.commit()
    except Exception as e:
        logger.error(f"History error: {e}")

# ================== Core Logic (UNCHANGED) ==================
async def process_flight_query(user_text, user_id=None):
    try:
        intent = intent_analyzer.analyze_intent(user_text)

        if intent["intent"] in ["gibberish", "greeting", "thanks", "general_question", "help", "unclear"]:
            return intent["response"]

        nlp_result = nlp_engine.process_query(user_text)
        should_call = intent_analyzer.should_use_amadeus(intent, nlp_result)

        if should_call and nlp_result.get("success"):
            query = nlp_result["query"]

            with app.app_context():
                search_result = flight_system.search_flights_safe(
                    query["origin"],
                    query["destination"],
                    query["date"],
                    query["adults"]
                )

                formatted = flight_system.format_flight_results(search_result)
                response = flight_system.get_flight_response_messages(query, formatted)

                if user_id:
                    log_search_history(
                        user_id,
                        user_text,
                        nlp_result,
                        True,
                        formatted.get("count", 0)
                    )

                return response

        if not nlp_result.get("success"):
            missing = nlp_result.get("missing_info", [])
            if missing:
                return (
                    "✈️ أحتاج بعض المعلومات:\n"
                    f"📋 {', '.join(missing)}\n\n"
                    "مثال:\n"
                    "رحلة من الرياض إلى دبي يوم 15 ديسمبر لشخصين"
                )

        return "🤖 كيف أستطيع مساعدتك في البحث عن رحلة؟"

    except Exception as e:
        logger.error(f"Processing error: {e}")
        return "❌ حدث خطأ، حاول مرة أخرى."

# ================== Webhook Verify ==================
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Forbidden", 403

# ================== Webhook Receive ==================
@app.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    data = request.json
    logger.info(f"📩 Incoming: {data}")

    try:
        value = data["entry"][0]["changes"][0]["value"]
        if "messages" not in value:
            return "OK", 200

        message = value["messages"][0]
        user_text = message["text"]["body"]
        user_id = message["from"]

        reply = asyncio.run(process_flight_query(user_text, user_id))

        if isinstance(reply, list):
            for msg in reply:
                send_whatsapp_message(user_id, msg)
        else:
            send_whatsapp_message(user_id, reply)

    except Exception as e:
        logger.error(f"Webhook error: {e}")

    return "OK", 200

# ================== Run ==================
if __name__ == "__main__":
    setup_database()

    with app.app_context():
        flight_system.init_app(app)
        nlp_engine.init_app(app)
        try:
            flight_system.get_amadeus_token()
            logger.info("✅ Amadeus connected")
        except Exception as e:
            logger.warning(f"⚠️ Amadeus not available: {e}")

    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
