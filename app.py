# app.py
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import asyncio
import threading
import os

from models import db, SearchHistory, SystemSettings, APIUsage, init_db, add_initial_data
from models import City, Month, ArabicTextReplacement, Airline, Country
from nlp_engine import FlightNLP
# استيراد الكود الجديد بدلاً من القديم
from flight_system import flight_system, search_flights, get_cheapest_flight

from datetime import datetime
from intent_analyzer import IntentAnalyzer

# إنشاء محلل النوايا
intent_analyzer = IntentAnalyzer()

# إعدادات بوت التلقرام
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-123')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///flight_bot.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# تهيئة قاعدة البيانات أولاً
init_db(app)

# إنشاء الجداول وإضافة البيانات الافتراضية
def setup_database():
    """إعداد قاعدة البيانات والبيانات الأولية"""
    try:
        with app.app_context():
            # إنشاء جميع الجداول
            db.create_all()
            print("✅ تم إنشاء الجداول بنجاح")
            
            # إضافة البيانات الأولية
            add_initial_data()
            print("✅ تم إضافة البيانات الأولية بنجاح")
            
    except Exception as e:
        print(f"❌ خطأ في إعداد قاعدة البيانات: {e}")
        raise

# استدعاء إعداد قاعدة البيانات
setup_database()

# إنشاء instance من المحرك NLP بعد إنشاء قاعدة البيانات
nlp_engine = FlightNLP()

# تطبيق التلقرام
telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

async def handle_media_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل التي تحتوي على ملفات وسائط (صور/وثائق)"""
    try:
        user = update.message.from_user
        
        print(f"📎 استقبلت ملف وسائط من {user.first_name}")
        
        # الرد بأن النظام لا يدعم معالجة الصور
        response = (
            "📸 **ملاحظة حول الملفات المرسلة:**\n\n"
            "حالياً، النظام لا يدعم معالجة الصور أو المستندات.\n\n"
            "💡 **يرجى إدخال تفاصيل رحلتك نصياً مثل:**\n"
            "• رحلة من القاهرة إلى دبي يوم 25 نوفمبر\n"
            "• أريد السفر من الرياض إلى اسطنبول غداً\n"
            "• ابحث عن تذاكر من جدة إلى لندن لشخصين\n\n"
            "**تنسيقات مدعومة:**\n"
            "• رحلة من [المدينة] إلى [الوجهة] في [التاريخ]\n"
            "• سفر من [رمز المطار] إلى [رمز المطار] [التاريخ]\n"
            "• ابحث عن رحلات من [المدينة] إلى [الوجهة]"
        )
        
        await update.message.reply_text(response, parse_mode='Markdown')
            
    except Exception as e:
        print(f"❌ خطأ في معالجة رسالة الوسائط: {e}")
        await update.message.reply_text("❌ حدث خطأ في معالجة الرسالة. يرجى المحاولة مرة أخرى.")

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
        print(f"Failed to log search history: {e}")
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
        print(f"Error processing flight query: {e}")
        return "❌ حدث خطأ أثناء معالجة طلبك. يرجى المحاولة مرة أخرى."

async def telegram_auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دالة الرد التلقائي على رسائل التلقرام"""
    try:
        user = update.message.from_user
        user_text = update.message.text
        
        print(f"📩 رسالة من {user.first_name}: {user_text}")
        
        # معالجة الاستعلام باستخدام نظامك
        reply_message = await process_flight_query(user_text, user_id=str(user.id))
        
        # إرسال الرد
        if isinstance(reply_message, list):
            for msg in reply_message:
                await update.message.reply_text(msg, parse_mode='Markdown')
        else:
            await update.message.reply_text(reply_message, parse_mode='Markdown')
        
        print(f"✅ تم الرد على {user.first_name}")
        
    except Exception as e:
        print(f"❌ خطأ في معالجة رسالة التلقرام: {e}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى.")

def setup_telegram_handlers():
    """إعداد معالجات رسائل التلقرام"""
    # إضافة مستمع للرسائل النصية (يستثني الأوامر)
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, telegram_auto_reply))

    # معالجة الصور والمستندات للرد بأن النظام لا يدعمها
    telegram_app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE | filters.Document.ALL, handle_media_message))

    print("✅ تم إعداد معالجات رسائل التلقرام")

def run_telegram_bot():
    """تشغيل بوت التلقرام في thread منفصل"""
    print("🤖 بدء تشغيل بوت التلقرام...")
    setup_telegram_handlers()
    telegram_app.run_polling()

# Routes
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'Flight Bot + Telegram'})

@app.route('/api/process-query', methods=['POST'])
def api_process_query():
    """واجهة API لمعالجة الاستفسارات - النسخة المصلحة"""
    start_time = datetime.now()
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            response_time = (datetime.now() - start_time).total_seconds()
            return jsonify({
                'success': False,
                'error': 'يجب تقديم نص الاستفسار في حقل "text"'
            }), 400
        
        user_text = data['text']
        user_id = data.get('user_id', 'api_user')
        
        # استخدام الدالة الجديدة للمعالجة
        response = asyncio.run(process_flight_query(user_text, user_id))
        
        return jsonify({
            'success': True,
            'response': response,
            'processing_time': (datetime.now() - start_time).total_seconds()
        })
    
    except Exception as e:
        response_time = (datetime.now() - start_time).total_seconds()
        return jsonify({
            'success': False,
            'error': f'خطأ في الخادم: {str(e)}',
            'processing_time': response_time
        }), 500

@app.route('/api/test-intent', methods=['POST'])
def test_intent():
    """واجهة لاختبار نظام النوايا"""
    data = request.get_json()
    text = data.get('text', '')
    
    intent_result = intent_analyzer.analyze_intent(text)
    nlp_result = nlp_engine.process_query(text)
    should_use_amadeus = intent_analyzer.should_use_amadeus(intent_result, nlp_result)
    
    return jsonify({
        'text': text,
        'intent_analysis': intent_result,
        'nlp_analysis': nlp_result,
        'should_use_amadeus': should_use_amadeus
    })

@app.route('/bot-status', methods=['GET'])
def bot_status():
    """فحص حالة البوت"""
    return jsonify({
        'telegram_bot': 'running',
        'flask_app': 'running',
        'service': 'Flight Booking Assistant'
    })

@app.route('/db-status', methods=['GET'])
def db_status():
    """فحص حالة قاعدة البيانات"""
    try:
        with app.app_context():
            essential_data = check_essential_data()
            return jsonify({
                'database': 'connected',
                'tables_created': True,
                'essential_data': essential_data
            })
    except Exception as e:
        return jsonify({
            'database': 'error',
            'error': str(e)
        }), 500

# وظيفة مساعدة للتحقق من وجود بيانات أساسية
def check_essential_data():
    """التحقق من وجود البيانات الأساسية في النظام"""
    try:
        with app.app_context():
            essential_data = {
                'cities': City.query.count(),
                'months': Month.query.count(),
                'text_replacements': ArabicTextReplacement.query.count(),
                'airlines': Airline.query.count(),
                'countries': Country.query.count()
            }
            return essential_data
    except Exception as e:
        print(f"❌ خطأ في التحقق من البيانات الأساسية: {e}")
        return {
            'cities': 0,
            'months': 0,
            'text_replacements': 0,
            'airlines': 0,
            'countries': 0
        }

# إضافة route جديد لاختبار النظام الجديد
@app.route('/api/test-flight-search', methods=['POST'])
def test_flight_search():
    """واجهة لاختبار البحث في النظام الجديد"""
    try:
        data = request.get_json()
        origin = data.get('origin', 'الرياض')
        destination = data.get('destination', 'دبي')
        date = data.get('date', '2024-12-20')
        adults = data.get('adults', 1)
        
        with app.app_context():
            # استخدام النظام الجديد مباشرة
            search_result = flight_system.search_flights_safe(origin, destination, date, adults)
            formatted_results = flight_system.format_flight_results(search_result)
            
            return jsonify({
                'success': True,
                'search_result': {
                    'origin_airports': search_result.get('origin_airports', []),
                    'destination_airports': search_result.get('destination_airports', []),
                    'total_flights_found': len(search_result.get('flights_data', []))
                },
                'formatted_results': formatted_results
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 بدء تشغيل تطبيق Flight Bot...")
    
    # التحقق من حالة قاعدة البيانات
    try:
        with app.app_context():
            # تهيئة النظام الجديد مع التطبيق داخل سياق التطبيق
            flight_system.init_app(app)
            
            # تهيئة NLP مع التطبيق داخل سياق التطبيق
            nlp_engine.init_app(app)
            
    except Exception as e:
        print(f"❌ خطأ في التحقق من قاعدة البيانات: {e}")
        # محاولة إعادة إنشاء الجداول
        setup_database()
    
    # اختبار الاتصال بـ Amadeus (استخدام النظام الجديد)
    try:
        with app.app_context():
            token = flight_system.get_amadeus_token()
            print("✅ الاتصال بـ Amadeus API ناجح")
    except Exception as e:
        print(f"⚠️ تحذير: فشل الاتصال بـ Amadeus API: {e}")
        print("ℹ️ النظام سيعمل ولكن بدون نتائج حقيقية من Amadeus")
    
    # تشغيل بوت التلقرام في thread منفصل
    telegram_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    telegram_thread.start()
    print("✅ بدأ تشغيل بوت التلقرام في الخلفية")
    
    # تشغيل تطبيق Flask
    print("🌐 بدأ تشغيل تطبيق Flask على المنفذ 5000")
    app.run(host='0.0.0.0', port=5000, debug=False)