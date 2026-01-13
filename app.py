# app.py
import os
import logging
from flask import Flask, request, jsonify, render_template
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import asyncio
import threading
import sys

from models import db, SearchHistory, SystemSettings, APIUsage, init_db, add_initial_data
from models import City, Month, ArabicTextReplacement, Airline, Country
from nlp_engine import FlightNLP
from flight_system import flight_system, search_flights, get_cheapest_flight
from datetime import datetime
from intent_analyzer import IntentAnalyzer

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# إنشاء محلل النوايا
intent_analyzer = IntentAnalyzer()

# إعدادات Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-123')

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'sqlite:///' + os.path.join(basedir, 'flight_bot.db')
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# إعداد قاعدة البيانات
init_db(app)

# إنشاء instance من المحرك NLP بعد إنشاء قاعدة البيانات
nlp_engine = FlightNLP()

def setup_database():
    """إعداد قاعدة البيانات والبيانات الأولية"""
    try:
        with app.app_context():
            # إنشاء جميع الجداول
            db.create_all()
            logger.info("✅ تم إنشاء الجداول بنجاح")
            
            # إضافة البيانات الأولية
            add_initial_data()
            logger.info("✅ تم إضافة البيانات الأولية بنجاح")
            
    except Exception as e:
        logger.error(f"❌ خطأ في إعداد قاعدة البيانات: {e}")
        raise

def log_search_history(user_id, query_text, nlp_result, success, flights_found=0):
    """تسجيل تاريخ البحث"""
    try:
        with app.app_context():
            search = SearchHistory(
                user_id=user_id,
                query_text=query_text,
                success=success,
                flights_found=flights_found
            )
            
            if nlp_result.get('query'):
                query = nlp_result['query']
                search.origin = query['origin']
                search.destination = query['destination']
                search.flight_date = datetime.strptime(query['date'], '%Y-%m-%d').date()
                search.passengers = query['adults']
            
            search.set_nlp_result(nlp_result)
            db.session.add(search)
            db.session.commit()
            return search.id
    except Exception as e:
        logger.error(f"Failed to log search history: {e}")
        return None

async def process_flight_query(user_text, user_id=None):
    """معالجة استعلام رحلة طيران وإرجاع الرد المناسب"""
    try:
        start_time = datetime.now()
        
        # 1. تحليل النية أولاً
        intent_result = intent_analyzer.analyze_intent(user_text)
        
        # 2. إذا كانت نية غير مفهومة تماماً - رد مباشر
        if intent_result['intent'] in ['gibberish']:
            return intent_result['response']
        
        # 3. إذا كانت نية مباشرة (تحية، شكر، إلخ) - رد مباشر بدون Amadeus
        if intent_result['intent'] in ['greeting', 'thanks', 'general_question', 'help', 'unclear']:
            return intent_result['response']
        
        # 4. إذا كانت نية بحث عن رحلة أو نص مقبول، استخدم NLP
        nlp_result = nlp_engine.process_query(user_text)
        
        # 5. تحديد ما إذا كان يجب استخدام Amadeus
        should_call_amadeus = intent_analyzer.should_use_amadeus(intent_result, nlp_result)
        
        # 6. استدعاء Amadeus فقط إذا لزم الأمر
        if should_call_amadeus and nlp_result.get('success'):
            query = nlp_result['query']
            
            # استخدام النظام الجديد للبحث عن الرحلات داخل سياق التطبيق
            with app.app_context():
                # استخدام الدالة المعدلة من flight_system
                search_result = flight_system.search_flights_safe(
                    query['origin'],
                    query['destination'], 
                    query['date'],
                    query['adults']
                )
                
                # استخدام الدالة المعدلة للتنسيق
                formatted_results = flight_system.format_flight_results(search_result)
                
                # استخدام الدالة المعدلة للحصول على الرد (قائمة رسائل)
                response = flight_system.get_flight_response_messages(query, formatted_results)
                
                # تسجيل البحث في التاريخ
                if user_id:
                    flights_found = formatted_results.get('count', 0)
                    log_search_history(user_id, user_text, nlp_result, True, flights_found)
                
                return response
        
        # 7. إذا فشل NLP ولكن النية كانت مقبولة
        elif not nlp_result.get('success') and intent_result['intent'] in ['flight_search', 'unknown_but_acceptable']:
            missing_info = nlp_result.get('missing_info', [])
            if missing_info:
                response = (
                    "✈️ أرى أنك تبحث عن رحلة طيران!\n\n"
                    "لكنني أحتاج بعض المعلومات الإضافية:\n"
                    f"📋 {', '.join(missing_info)}\n\n"
                    "💡 **مثال:**\n"
                    "\"رحلة من الرياض إلى دبي يوم 15 ديسمبر لشخصين\""
                )
            else:
                response = (
                    "🤔 لم أستطع فهم تفاصيل رحلتك بشكل كامل.\n\n"
                    "💡 **جرب صيغة مثل:**\n"
                    "\"رحلة من [مدينتك] إلى [الوجهة] في [التاريخ]\"\n\n"
                    "**أمثلة:**\n"
                    "• رحلة من جدة إلى اسطنبول 20 يناير\n"
                    "• أريد السفر من الرياض إلى دبي غدا\n"
                    "• ابحث عن تذاكر من الدمام إلى القاهرة"
                )
            return response
        
        # 8. الرد الافتراضي
        return "🤖 أنا مساعدك للبحث عن رحلات الطيران. كيف يمكنني مساعدتك؟\n\n💡 **جرب أن تسألني عن:**\n• رحلات من مدينتك إلى وجهة أحلامك\n• أسعار تذاكر الطيران\n• توفر الرحلات في تاريخ محدد"
    
    except Exception as e:
        logger.error(f"Error processing flight query: {e}")
        return "❌ حدث خطأ أثناء معالجة طلبك. يرجى المحاولة مرة أخرى."

async def telegram_auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دالة الرد التلقائي على رسائل التلقرام"""
    try:
        user = update.message.from_user
        user_text = update.message.text
        
        logger.info(f"📩 رسالة من {user.first_name}: {user_text}")
        
        # معالجة الاستعلام باستخدام نظامك
        reply_message = await process_flight_query(user_text, user_id=str(user.id))
        
        # إرسال الرد
        if isinstance(reply_message, list):
            for msg in reply_message:
                await update.message.reply_text(msg, parse_mode='Markdown')
        else:
            await update.message.reply_text(reply_message, parse_mode='Markdown')
        
        logger.info(f"✅ تم الرد على {user.first_name}")
        
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة رسالة التلقرام: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى.")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة أمر /start"""
    welcome_message = """
    ✈️ **مرحباً بك في بوت البحث عن رحلات الطيران!**

    أنا مساعدك الذكي للبحث عن:
    • 🎫 تذاكر الطيران بأفضل الأسعار
    • 📅 رحلات في تواريخ محددة
    • 🌍 وجهات سفر مختلفة حول العالم

    **💡 كيف تستخدم البوت:**
    فقط اكتب رسالة مثل:
    • "أريد رحلة من الرياض إلى دبي يوم 15 يناير"
    • "ابحث عن تذاكر من جدة إلى اسطنبول"
    • "رحلة من القاهرة إلى لندن غداً"

    **🛠️ أوامر متاحة:**
    /start - عرض هذه الرسالة
    /help - المساعدة والأمثلة

    ابدأ بالكتابة الآن! 🚀
    """
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة أمر /help"""
    help_message = """
    🆘 **مساعدة استخدام البوت**

    **📝 أمثلة على الاستخدام:**
    1. بحث بسيط:
       "رحلة من الرياض إلى دبي"

    2. بحث بتاريخ:
       "أريد تذكرة من جدة إلى اسطنبول يوم 20 فبراير"

    3. بحث بعدد المسافرين:
       "رحله من القاهرة إلى لندن لثلاث أشخاص"

    4. بحث بتفاصيل كاملة:
       "ابحث عن رحلة من الدمام إلى أبوظبي غداً لشخصين"

    **🔍 نصائح للبحث:**
    • استخدم المدن الرئيسية (الرياض، جدة، دبي، إلخ)
    • يمكنك استخدام التواريخ بالأرقام أو الأشهر
    • يمكنك استخدام "غداً" أو "بعد غد"

    **🛠️ الأوامر المتاحة:**
    /start - بدء البوت
    /help - هذه الرسالة

    اكتب استفسارك الآن وسأساعدك! ✨
    """
    await update.message.reply_text(help_message, parse_mode='Markdown')

def run_flask_app():
    """تشغيل تطبيق Flask في thread منفصل"""
    try:
        # إعداد قاعدة البيانات
        setup_database()
        
        # تهيئة الأنظمة داخل سياق التطبيق
        with app.app_context():
            flight_system.init_app(app)
            nlp_engine.init_app(app)
            
            # اختبار الاتصال بـ Amadeus
            try:
                token = flight_system.get_amadeus_token()
                logger.info("✅ الاتصال بـ Amadeus API ناجح")
            except Exception as e:
                logger.warning(f"⚠️ تحذير: فشل الاتصال بـ Amadeus API: {e}")
                logger.info("ℹ️ النظام سيعمل ولكن بدون نتائج حقيقية من Amadeus")
        
        # تشغيل Flask
        port = int(os.getenv('PORT', 5000))
        debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        
        logger.info(f"🌐 بدأ تشغيل تطبيق Flask على المنفذ {port}")
        app.run(
            host='0.0.0.0',
            port=port,
            debug=debug_mode,
            use_reloader=False
        )
    except Exception as e:
        logger.error(f"❌ فشل تشغيل Flask: {e}")

def main():
    """الدالة الرئيسية لتشغيل التطبيق"""
    # التحقق من وجود التوكن
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not found!")
        print("=" * 50)
        print("❌ خطأ: لم يتم العثور على BOT_TOKEN")
        print("الرجاء التأكد من تعيين متغير البيئة BOT_TOKEN")
        print("=" * 50)
        return
    
    # إنشاء تطبيق التلقرام
    telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # إضافة المعالجات
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, telegram_auto_reply))
    telegram_app.add_handler(MessageHandler(filters.COMMAND, start_command), group=0)
    telegram_app.add_handler(MessageHandler(filters.COMMAND, help_command), group=0)
    
    # بدء تشغيل Flask في thread منفصل
    flask_thread = threading.Thread(target=run_flask_app, daemon=True)
    flask_thread.start()
    
    # عرض معلومات البدء
    print("=" * 50)
    print("🚀 Flight Bot System is running")
    print("🤖 Telegram Bot: Active with POLLING")
    print("🌐 Flask Web Server: Active on port 5000")
    print("✅ System will stay active (Render Worker)")
    print("=" * 50)
    logger.info("🚀 Starting bot with polling...")
    
    # تشغيل البوت مع Polling
    telegram_app.run_polling(
        drop_pending_updates=True,
        allowed_updates=['message'],
        close_loop=False
    )

if __name__ == '__main__':
    main()