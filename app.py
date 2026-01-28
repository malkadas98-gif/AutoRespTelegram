import os
import logging
import requests
import asyncio
import time
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
WHATSAPP_API_URL = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

# ================== WhatsApp Message Templates ==================
class WhatsAppTemplates:
    @staticmethod
    def welcome_message():
        return """🛫 *مرحباً بك في نظام حجز الطيران الذكي*

أنا مساعدك الذكي للبحث عن الرحلات الجوية. يمكنني مساعدتك في:

✈️ *البحث عن الرحلات*
🔍 *مقارنة الأسعار*
📅 *البحث حسب التاريخ*
🏙️ *البحث حسب المدينة*

*📝 مثال للبحث:*
• رحلة من الرياض إلى دبي يوم 15 ديسمبر لشخصين
• أريد السفر من جدة إلى القاهرة غداً
• ابحث عن رحلات من الدمام إلى البحرين 2025-01-20

*💡 تذكر:* اذكر دائماً:
1. مدينة المغادرة
2. مدينة الوصول
3. تاريخ السفر
4. عدد المسافرين

كيف يمكنني مساعدتك اليوم؟"""

    @staticmethod
    def flight_results_summary(query, flights_count, lowest_price):
        return f"""✅ *تم العثور على {flights_count} رحلة*

*تفاصيل البحث:*
📍 المغادرة: {query.get('origin', 'غير محدد')}
🎯 الوصول: {query.get('destination', 'غير محدد')}
📅 التاريخ: {query.get('date', 'غير محدد')}
👥 المسافرون: {query.get('adults', 1)} شخص

💰 *أقل سعر متوفر:* {lowest_price} ريال

سأرسل لك الآن أفضل 3 رحلات..."""

    @staticmethod
    def single_flight_details(flight, index):
        return f"""*الرحلة {index + 1}*

✈️ *الخطوط:* {flight.get('airline', 'غير محدد')}
🛫 *المغادرة:* {flight.get('departure_time', 'غير محدد')}
🛬 *الوصول:* {flight.get('arrival_time', 'غير محدد')}
⏱️ *المدة:* {flight.get('duration', 'غير محدد')}
💰 *السعر:* {flight.get('price', 'غير محدد')} ريال
🔢 *رقم الرحلة:* {flight.get('flight_number', 'غير محدد')}"""

    @staticmethod
    def missing_info_message(missing_fields):
        fields_arabic = {
            'origin': 'مدينة المغادرة',
            'destination': 'مدينة الوصول',
            'date': 'تاريخ السفر',
            'adults': 'عدد المسافرين'
        }
        
        missing_list = [fields_arabic.get(field, field) for field in missing_fields]
        
        return f"""✈️ *أحتاج بعض المعلومات الإضافية*

📋 *المعلومات الناقصة:*
{chr(10).join([f'• {item}' for item in missing_list])}

*📝 مثال:*
"رحلة من {missing_fields[0] if 'origin' in missing_fields else 'الرياض'} إلى {missing_fields[1] if 'destination' in missing_fields else 'دبي'} يوم 15 ديسمبر لشخصين"

يرجى إرسال المعلومات المطلوبة."""

    @staticmethod
    def no_flights_found(query):
        return f"""❌ *لم أجد رحلات متاحة*

*بحثت عن:*
📍 {query.get('origin', 'غير محدد')} → 🎯 {query.get('destination', 'غير محدد')}
📅 {query.get('date', 'غير محدد')}
👥 {query.get('adults', 1)} شخص

*💡 اقتراحات:*
• حاول تغيير تاريخ السفر
• تحقق من أسماء المدنين
• جرب البحث عن رحلات في يوم آخر

هل ترغب في البحث بتواريخ أخرى؟"""

# ================== WhatsApp Send Functions ==================
def send_whatsapp_message(to, text):
    """إرسال رسالة نصية عادية"""
    try:
        headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {
                "body": text,
                "preview_url": False
            }
        }
        
        response = requests.post(WHATSAPP_API_URL, headers=headers, json=payload)
        
        if response.status_code == 200:
            logger.info(f"✅ WhatsApp message sent to {to}")
            return True
        else:
            logger.error(f"❌ Failed to send WhatsApp message: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error sending WhatsApp message: {str(e)}")
        return False

def send_whatsapp_template(to, template_name, language_code="ar", components=None):
    """إرسال قالب رسالة"""
    try:
        headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language_code
                }
            }
        }
        
        if components:
            payload["template"]["components"] = components
        
        response = requests.post(WHATSAPP_API_URL, headers=headers, json=payload)
        return response.json()
        
    except Exception as e:
        logger.error(f"❌ Error sending template: {str(e)}")
        return None

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
            logger.info(f"📊 Search logged for user {user_id}")
    except Exception as e:
        logger.error(f"❌ History error: {e}")

# ================== Core Processing ==================
async def process_flight_query(user_text, user_id=None, whatsapp_number=None):
    """معالجة استعلام المستخدم وإرجاع الرد المناسب"""
    try:
        logger.info(f"🔍 Processing query from {user_id}: {user_text}")
        
        # تحليل النية
        intent = intent_analyzer.analyze_intent(user_text)
        logger.info(f"🎯 Intent detected: {intent['intent']}")
        
        # معالجة الردود التلقائية
        if intent["intent"] in ["gibberish", "greeting", "thanks", "general_question", "help", "unclear"]:
            if intent["intent"] == "greeting":
                return WhatsAppTemplates.welcome_message()
            return intent["response"]
        
        # معالجة استعلامات الرحلات
        nlp_result = nlp_engine.process_query(user_text)
        logger.info(f"🤖 NLP Result: {nlp_result}")
        
        should_call = intent_analyzer.should_use_amadeus(intent, nlp_result)
        
        if should_call and nlp_result.get("success"):
            query = nlp_result["query"]
            
            with app.app_context():
                # البحث عن الرحلات
                search_result = flight_system.search_flights_safe(
                    query["origin"],
                    query["destination"],
                    query["date"],
                    query["adults"]
                )
                
                # تنسيق النتائج
                formatted = flight_system.format_flight_results(search_result)
                
                # تسجيل البحث
                if user_id:
                    log_search_history(
                        user_id,
                        user_text,
                        nlp_result,
                        True,
                        formatted.get("count", 0)
                    )
                
                # إعداد الردود للواتساب
                return prepare_whatsapp_response(query, formatted, nlp_result)
        
        # إذا كان هناك معلومات ناقصة
        if not nlp_result.get("success"):
            missing = nlp_result.get("missing_info", [])
            if missing:
                return WhatsAppTemplates.missing_info_message(missing)
        
        # رد افتراضي
        return "🤖 كيف أستطيع مساعدتك في البحث عن رحلة؟"
        
    except Exception as e:
        logger.error(f"❌ Processing error: {e}")
        return "❌ عذراً، حدث خطأ أثناء معالجة طلبك. يرجى المحاولة مرة أخرى."

def prepare_whatsapp_response(query, flight_results, nlp_result):
    """إعداد الردود المناسبة للواتساب"""
    responses = []
    
    if flight_results.get("count", 0) > 0:
        # ملخص النتائج
        summary = WhatsAppTemplates.flight_results_summary(
            query, 
            flight_results["count"],
            flight_results.get("lowest_price", "غير متوفر")
        )
        responses.append(summary)
        
        # أفضل 3 رحلات
        flights = flight_results.get("flights", [])[:3]
        for i, flight in enumerate(flights):
            flight_detail = WhatsAppTemplates.single_flight_details(flight, i)
            responses.append(flight_detail)
        
        # رسالة ختامية
        responses.append("""📌 *للحجز أو لمزيد من المعلومات:*
• تفضل بزيارة موقعنا الإلكتروني
• أو اتصل بخدمة العملاء

هل ترغب في البحث عن رحلات أخرى؟""")
        
    else:
        # لا توجد رحلات
        responses.append(WhatsAppTemplates.no_flights_found(query))
    
    return responses

@app.route("/test-verify", methods=["GET"])
def test_verify():
    """اختبار التحقق يدوياً"""
    token = request.args.get("token")
    
    if token == VERIFY_TOKEN:
        return jsonify({
            "status": "success",
            "message": "Token matches!",
            "your_token": VERIFY_TOKEN[:5] + "..." if VERIFY_TOKEN else None,
            "received_token": token
        })
    else:
        return jsonify({
            "status": "failed",
            "message": "Token mismatch!",
            "your_token": VERIFY_TOKEN,
            "received_token": token
        })
    
# ================== Webhook Verify ==================
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """التحقق من صحة webhook"""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    logger.info(f"🔍 Webhook verification attempt: mode={mode}, token={token}")
    
    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            logger.info("✅ Webhook verified successfully!")
            return challenge, 200
        else:
            logger.error("❌ Verification failed: Invalid token")
            return "Forbidden", 403
    
    return "Bad Request", 400

# ================== Webhook Receive ==================
@app.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    """استقبال رسائل الواتساب"""
    try:
        data = request.get_json()
        logger.info(f"📩 Incoming webhook data")
        
        if data.get("object") != "whatsapp_business_account":
            return jsonify({"status": "ignored"}), 200
        
        entries = data.get("entry", [])
        
        for entry in entries:
            changes = entry.get("changes", [])
            
            for change in changes:
                value = change.get("value", {})
                
                # معالجة الرسائل الواردة
                if "messages" in value:
                    messages = value.get("messages", [])
                    
                    for message in messages:
                        if message.get("type") == "text":
                            user_text = message["text"]["body"]
                            user_id = message["from"]
                            message_id = message["id"]
                            
                            logger.info(f"👤 Message from {user_id}: {user_text}")
                            
                            # معالجة الرسالة
                            response = asyncio.run(process_flight_query(user_text, user_id))
                            
                            # إرسال الرد
                            if isinstance(response, list):
                                for msg in response:
                                    send_whatsapp_message(user_id, msg)
                                    # تأخير بسيط بين الرسائل
                                    time.sleep(0.5)
                            else:
                                send_whatsapp_message(user_id, response)
                
                # معالجة حالة الرسالة
                elif "statuses" in value:
                    statuses = value.get("statuses", [])
                    for status in statuses:
                        logger.info(f"📊 Message status: {status.get('status')} for {status.get('recipient_id')}")
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        logger.error(f"❌ Webhook error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ================== Test Endpoints ==================
@app.route("/send-test", methods=["GET"])
def send_test_message():
    """نقطة نهاية لاختبار إرسال رسالة"""
    try:
        test_number = request.args.get("to")
        test_message = request.args.get("message", "Test message from flight bot")
        
        if not test_number:
            return jsonify({"error": "Missing 'to' parameter"}), 400
        
        success = send_whatsapp_message(test_number, test_message)
        
        if success:
            return jsonify({
                "status": "success",
                "message": "Test message sent"
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to send message"
            }), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/check-config", methods=["GET"])
def check_config():
    """التحقق من إعدادات النظام"""
    return jsonify({
        "whatsapp_configured": bool(WHATSAPP_TOKEN and PHONE_NUMBER_ID),
        "database_configured": bool(app.config["SQLALCHEMY_DATABASE_URI"]),
        "whatsapp_token_length": len(WHATSAPP_TOKEN) if WHATSAPP_TOKEN else 0,
        "phone_number_id": PHONE_NUMBER_ID
    })


# ================== Debug Endpoint ==================
@app.route("/debug/message", methods=["POST"])
def debug_message():
    """نقطة نهاية للاختبار المباشر"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        user_text = data.get("text", "")
        user_id = data.get("user_id", "test_user")
        
        if not user_text:
            return jsonify({"error": "Missing 'text' parameter"}), 400
        
        # معالجة الرسالة
        response = asyncio.run(process_flight_query(user_text, user_id))
        
        return jsonify({
            "success": True,
            "original_message": user_text,
            "response": response,
            "response_type": "list" if isinstance(response, list) else "text"
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Debug error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/debug/send-whatsapp", methods=["POST"])
def debug_send_whatsapp():
    """اختبار إرسال واتساب مباشر"""
    try:
        data = request.get_json()
        
        to = data.get("to")
        message = data.get("message", "Test message")
        
        if not to:
            return jsonify({"error": "Missing 'to' parameter"}), 400
        
        success = send_whatsapp_message(to, message)
        
        return jsonify({
            "success": success,
            "to": to,
            "message": message
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ================== Simulated Webhook ==================
@app.route("/simulate-webhook", methods=["POST"])
def simulate_webhook():
    """محاكاة استقبال ويب هوك للاختبار"""
    try:
        data = request.get_json()
        
        # محاكاة بيانات الويب هوك
        simulated_data = {
            "object": "whatsapp_business_account",
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": data.get("from", "201234567890"),
                            "id": "test_" + datetime.now().strftime("%Y%m%d%H%M%S"),
                            "timestamp": str(int(datetime.now().timestamp())),
                            "text": {
                                "body": data.get("text", "Test message")
                            },
                            "type": "text"
                        }]
                    }
                }]
            }]
        }
        
        # معالجة البيانات
        return whatsapp_webhook_with_data(simulated_data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def whatsapp_webhook_with_data(data):
    """نسخة معزولة من ويب هوك للاختبار"""
    try:
        if data.get("object") != "whatsapp_business_account":
            return jsonify({"status": "ignored"}), 200
        
        entries = data.get("entry", [])
        
        for entry in entries:
            changes = entry.get("changes", [])
            
            for change in changes:
                value = change.get("value", {})
                
                if "messages" in value:
                    messages = value.get("messages", [])
                    
                    for message in messages:
                        if message.get("type") == "text":
                            user_text = message["text"]["body"]
                            user_id = message["from"]
                            
                            logger.info(f"🔍 Simulated message from {user_id}: {user_text}")
                            
                            # معالجة الرسالة
                            response = asyncio.run(process_flight_query(user_text, user_id))
                            
                            return jsonify({
                                "processed": True,
                                "user_id": user_id,
                                "user_message": user_text,
                                "bot_response": response,
                                "response_sent": True if response else False
                            }), 200
        
        return jsonify({"status": "no_messages"}), 200
        
    except Exception as e:
        logger.error(f"❌ Simulated webhook error: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
# ================== Run Application ==================
if __name__ == "__main__":
    # التحقق من المتغيرات البيئية
    required_vars = ["WHATSAPP_TOKEN", "PHONE_NUMBER_ID", "VERIFY_TOKEN"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Missing environment variables: {missing_vars}")
        logger.error("Please set them in your .env file")
    else:
        logger.info("✅ All required environment variables are set")
        
        # إعداد قاعدة البيانات
        setup_database()
        
        with app.app_context():
            # تهئة الأنظمة
            flight_system.init_app(app)
            nlp_engine.init_app(app)
            
            # التحقق من اتصال Amadeus
            try:
                flight_system.get_amadeus_token()
                logger.info("✅ Amadeus API connected successfully")
            except Exception as e:
                logger.warning(f"⚠️ Amadeus API not available: {e}")
        
        # تشغيل التطبيق
        port = int(os.getenv("PORT", 5000))
        logger.info(f"🚀 Starting Flight WhatsApp Bot on port {port}")
        app.run(host="0.0.0.0", port=port, debug=True)