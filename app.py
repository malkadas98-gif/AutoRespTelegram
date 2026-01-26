import os
import sys
import logging
import requests
import asyncio
import json
from flask import Flask, request, jsonify
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
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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

# ================== WhatsApp Business API Configuration ==================
WHATSAPP_API_URL = "https://graph.facebook.com/v18.0"  # أحدث إصدار
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")  # Access Token من Facebook Developer
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")  # Phone Number ID
WHATSAPP_BUSINESS_ACCOUNT_ID = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID")  # Business Account ID
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "flight-bot-verify")  # للتحقق من Webhook

# ================== WhatsApp API Functions ==================
def send_whatsapp_message(to_number, message_text, message_type="text"):
    """
    إرسال رسالة واتساب باستخدام WhatsApp Business API مباشرة
    """
    if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        logger.error("❌ WhatsApp credentials missing")
        return None
    
    try:
        url = f"{WHATSAPP_API_URL}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
        
        headers = {
            "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # بناء payload الرسالة
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": message_type
        }
        
        if message_type == "text":
            payload["text"] = {"body": message_text}
        elif message_type == "template":
            # لرسائل القوالب (مطلوب موافقة من Meta)
            payload["template"] = message_text
        
        logger.info(f"📤 Sending WhatsApp to {to_number}: {message_text[:50]}...")
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            message_id = result.get("messages", [{}])[0].get("id")
            logger.info(f"✅ WhatsApp sent successfully! Message ID: {message_id}")
            
            # تسجيل الاستخدام في قاعدة البيانات
            log_api_usage("whatsapp_send", url, payload, result, True)
            
            return message_id
        else:
            error_msg = f"Failed to send WhatsApp: {response.status_code} - {response.text}"
            logger.error(f"❌ {error_msg}")
            
            # تسجيل الخطأ
            log_api_usage("whatsapp_send", url, payload, 
                         {"error": error_msg, "status_code": response.status_code}, False)
            
            # محاولة إرسال رسالة خطأ للمستخدم
            send_error_message(to_number)
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Network error sending WhatsApp: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Unexpected error sending WhatsApp: {e}", exc_info=True)
        return None

def send_error_message(to_number):
    """
    إرسال رسالة خطأ بديلة عند فشل الإرسال
    """
    try:
        error_text = "⚠️ عذراً، حدث خطأ في النظام. يرجى المحاولة مرة أخرى لاحقاً."
        send_whatsapp_message(to_number, error_text)
    except Exception as e:
        logger.error(f"Failed to send error message: {e}")

def log_api_usage(api_name, endpoint, request_data, response_data, success):
    """
    تسجيل استخدام API في قاعدة البيانات
    """
    try:
        with app.app_context():
            usage = APIUsage(
                api_name=api_name,
                endpoint=endpoint,
                request_data=json.dumps(request_data, ensure_ascii=False),
                response_data=json.dumps(response_data, ensure_ascii=False),
                success=success
            )
            db.session.add(usage)
            db.session.commit()
            logger.debug(f"📊 API usage logged for {api_name}")
    except Exception as e:
        logger.error(f"Failed to log API usage: {e}")

# ================== Database Setup ==================
def setup_database():
    with app.app_context():
        db.create_all()
        add_initial_data()
        logger.info("✅ Database initialized")

# ================== Search History ==================
def log_search_history(user_id, query_text, nlp_result, success, flights_found=0):
    try:
        with app.app_context():
            search = SearchHistory(
                user_id=f"whatsapp:{user_id}",
                query_text=query_text,
                success=success,
                flights_found=flights_found,
                platform="whatsapp_business_api"
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
            logger.info(f"📝 Search history logged for user {user_id}")
    except Exception as e:
        logger.error(f"History error: {e}")

# ================== Core Logic ==================
async def process_flight_query(user_text, user_id=None):
    """
    معالجة استعلام المستخدم وإرجاع الرد المناسب
    """
    try:
        logger.info(f"🔍 Processing query from {user_id}: {user_text}")
        
        # تحليل النية
        intent = intent_analyzer.analyze_intent(user_text)
        logger.info(f"🎯 Intent: {intent['intent']}")

        # ردود سريعة للنيّات البسيطة
        simple_intents = ["gibberish", "greeting", "thanks", "general_question", "help", "unclear"]
        if intent["intent"] in simple_intents:
            logger.info(f"📨 Returning simple response for {intent['intent']}")
            return intent["response"]

        # معالجة الاستعلام بالـ NLP
        nlp_result = nlp_engine.process_query(user_text)
        logger.info(f"🤖 NLP success: {nlp_result.get('success', False)}")
        
        # تحديد إذا كان يجب البحث في Amadeus
        should_call = intent_analyzer.should_use_amadeus(intent, nlp_result)
        
        if should_call and nlp_result.get("success"):
            query = nlp_result["query"]
            logger.info(f"✈️ Flight search: {query}")

            with app.app_context():
                # البحث عن الرحلات
                search_result = flight_system.search_flights_safe(
                    query["origin"],
                    query["destination"],
                    query["date"],
                    query["adults"]
                )
                
                flight_count = len(search_result.get('data', [])) if search_result.get('data') else 0
                logger.info(f"🔍 Found {flight_count} flights")

                if flight_count > 0:
                    formatted = flight_system.format_flight_results(search_result)
                    response = flight_system.get_flight_response_messages(query, formatted)
                    
                    # تسجيل البحث الناجح
                    if user_id:
                        log_search_history(user_id, user_text, nlp_result, True, flight_count)
                    
                    return response
                else:
                    # لا توجد رحلات
                    no_flights_msg = f"⚠️ لم أجد رحلات من {query['origin']} إلى {query['destination']} في {query['date']}"
                    return no_flights_msg

        # إذا كانت المعلومات ناقصة
        if not nlp_result.get("success"):
            missing = nlp_result.get("missing_info", [])
            if missing:
                missing_msg = (
                    "✈️ أحتاج بعض المعلومات للبحث:\n"
                    f"📋 {', '.join(missing)}\n\n"
                    "📌 مثال للبحث:\n"
                    "رحلة من الرياض إلى دبي يوم 15 ديسمبر لشخصين\n"
                    "أو\n"
                    "ابحث عن تذاكر من جدة إلى القاهرة يوم 20 يناير لـ 3 أشخاص"
                )
                return missing_msg

        # رد افتراضي
        return "🤖 كيف أستطيع مساعدتك في البحث عن رحلة؟\n\nمثال: 'ابحث عن رحلة من دبي إلى لندن لشخص واحد يوم 10 فبراير'"

    except Exception as e:
        logger.error(f"❌ Processing error: {e}", exc_info=True)
        return "❌ عذراً، حدث خطأ في النظام. يرجى المحاولة مرة أخرى."

# ================== Webhook Verification ==================
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """
    التحقق من Webhook مع Meta (مطلوب في إعدادات التطبيق)
    """
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    logger.info(f"🔐 Webhook verification attempt: mode={mode}, token={token}")
    
    if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
        logger.info("✅ Webhook verified successfully!")
        return challenge, 200
    
    logger.warning("❌ Webhook verification failed")
    return "Forbidden", 403

# ================== Webhook Handler ==================
@app.route("/webhook", methods=["POST"])
def handle_webhook():
    """
    معالجة رسائل الواتساب الواردة من Meta
    """
    try:
        data = request.get_json()
        logger.info(f"📩 Incoming webhook: {json.dumps(data, ensure_ascii=False)[:500]}...")
        
        if not data:
            logger.warning("⚠️ Empty webhook data")
            return jsonify({"status": "no data"}), 200
        
        # التحقق من أن الرسالة من واتساب
        if data.get("object") != "whatsapp_business_account":
            logger.warning("⚠️ Not a WhatsApp business account webhook")
            return jsonify({"status": "ignored"}), 200
        
        entries = data.get("entry", [])
        
        for entry in entries:
            changes = entry.get("changes", [])
            
            for change in changes:
                value = change.get("value", {})
                
                # معالجة الرسائل
                messages = value.get("messages", [])
                
                for message in messages:
                    # استخراج معلومات الرسالة
                    from_number = message.get("from", "")
                    message_type = message.get("type", "")
                    message_id = message.get("id", "")
                    
                    logger.info(f"📱 Message from {from_number}, type: {message_type}, id: {message_id}")
                    
                    # معالجة الرسائل النصية فقط حالياً
                    if message_type == "text":
                        message_text = message.get("text", {}).get("body", "")
                        
                        if message_text:
                            logger.info(f"📝 Text message: {message_text}")
                            
                            # معالجة الرسالة بشكل غير متزامن
                            reply = asyncio.run(process_flight_query(message_text, from_number))
                            
                            # إرسال الرد
                            if isinstance(reply, list):
                                for msg in reply:
                                    send_whatsapp_message(from_number, msg)
                                    asyncio.sleep(0.5)  # تأخير بين الرسائل
                            else:
                                send_whatsapp_message(from_number, reply)
                    
                    # يمكن إضافة معالجة لأنواع أخرى من الرسائل هنا
                    elif message_type == "interactive":
                        logger.info("🔄 Interactive message received")
                        # معالجة الرسائل التفاعلية (أزرار، قوائم)
                    
                    else:
                        logger.info(f"ℹ️ Unhandled message type: {message_type}")
                
                # معالجة حالة التسليم والقراءة (اختياري)
                statuses = value.get("statuses", [])
                for status in statuses:
                    status_info = f"📊 Message {status.get('id', 'unknown')} status: {status.get('status', 'unknown')}"
                    logger.info(status_info)
        
        return jsonify({"status": "processed"}), 200
        
    except Exception as e:
        logger.error(f"❌ Webhook processing error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

# ================== Health Check ==================
@app.route("/", methods=["GET"])
@app.route("/health", methods=["GET"])
def health_check():
    """
    نقطة فحص صحة الخدمة
    """
    whatsapp_status = "configured" if WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID else "not_configured"
    
    return jsonify({
        "status": "online",
        "service": "Flight Bot - WhatsApp Business API",
        "whatsapp": whatsapp_status,
        "timestamp": datetime.now().isoformat()
    }), 200

# ================== Test Endpoint ==================
@app.route("/test-message", methods=["POST"])
def test_message():
    """
    نقطة لاختبار إرسال رسالة (للاستخدام الداخلي فقط)
    """
    try:
        data = request.get_json()
        to_number = data.get("to")
        message = data.get("message", "Test message from Flight Bot")
        
        if not to_number:
            return jsonify({"error": "Missing 'to' number"}), 400
        
        result = send_whatsapp_message(to_number, message)
        
        if result:
            return jsonify({"success": True, "message_id": result}), 200
        else:
            return jsonify({"success": False, "error": "Failed to send"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ================== Run Application ==================
if __name__ == "__main__":
    # إعداد قاعدة البيانات
    setup_database()
    
    # تهيئة الأنظمة
    with app.app_context():
        flight_system.init_app(app)
        nlp_engine.init_app(app)
        
        # اختبار اتصال Amadeus
        try:
            flight_system.get_amadeus_token()
            logger.info("✅ Amadeus API connected successfully")
        except Exception as e:
            logger.warning(f"⚠️ Amadeus API not available: {e}")
    
    # عرض معلومات التهيئة
    logger.info("=" * 50)
    logger.info("🚀 Flight Bot WhatsApp Started")
    logger.info(f"📱 WhatsApp API: {'Configured' if WHATSAPP_ACCESS_TOKEN else 'Not Configured'}")
    logger.info(f"🌐 Webhook URL: https://your-render-url.onrender.com/webhook")
    logger.info(f"🔐 Verify Token: {WHATSAPP_VERIFY_TOKEN}")
    logger.info("=" * 50)
    
    # تشغيل التطبيق
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)