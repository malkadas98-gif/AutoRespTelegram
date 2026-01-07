from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import os
import threading
import asyncio

# إعدادات بوت التلقرام
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")  # لاحقاً للويب هوك

# إنشاء تطبيق Flask
app = Flask(__name__)

# تطبيق التلقرام
telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

# متغير لتعقب حالة البوت
bot_status = {
    "is_running": False,
    "last_message": None,
    "user_count": 0
}

# قائمة لتخزين آخر الرسائل (للتشخيص)
recent_messages = []

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل الواردة من Telegram"""
    try:
        user = update.message.from_user
        user_text = update.message.text
        
        # تحديث حالة البوت
        bot_status["last_message"] = {
            "user": user.first_name,
            "user_id": user.id,
            "text": user_text,
            "timestamp": update.message.date.isoformat()
        }
        
        # تخزين الرسالة الأخيرة
        recent_messages.append({
            "user": f"{user.first_name} (ID: {user.id})",
            "text": user_text[:100],
            "time": update.message.date.isoformat()
        })
        
        # حفظ آخر 10 رسائل فقط
        if len(recent_messages) > 10:
            recent_messages.pop(0)
        
        print(f"📩 رسالة من {user.first_name} (ID: {user.id}): {user_text}")
        
        # رد بسيط للتحقق
        response = f"""
✅ **تم استلام رسالتك بنجاح!**

👤 **المستخدم:** {user.first_name}
🆔 **معرف المستخدم:** {user.id}
📝 **نص الرسالة:** {user_text}

🤖 **حالة البوت:** نشط ✓
🔗 **التطبيق متصل على:** {WEBHOOK_URL or 'Polling Mode'}

📊 **إحصائيات البوت:**
• عدد المستخدمين: {bot_status['user_count']}
• آخر رسالة: الآن

💡 **لاختبار الواجهة:** انتقل إلى /bot-status
"""
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        print(f"❌ خطأ في معالجة الرسالة: {e}")
        if update.message:
            await update.message.reply_text("❌ حدث خطأ في معالجة رسالتك.")

def setup_telegram_handlers():
    """إعداد معالجات رسائل التلقرام"""
    try:
        # إضافة معالج للرسائل النصية
        telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # معالج للأوامر الأساسية
        from telegram.ext import CommandHandler
        
        async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """معالج أمر /start"""
            welcome_message = """
🚀 **مرحباً! تم تفعيل البوت بنجاح**

✅ **تم الاتصال بـ:**
• خادم Flask على Render
• قاعدة البيانات (إذا كانت متوفرة)
• نظام معالجة الرسائل

📊 **حالة النظام:**
• البوت: ✅ نشط
• الخادم: ✅ يعمل
• الاتصال: ✅ مستقر

🤖 **إمكانيات البوت:**
• استقبال الرسائل النصية
• الرد التلقائي
• تتبع حالة النظام

💡 **جرب إرسال أي رسالة وسأرد عليك!**
"""
            await update.message.reply_text(welcome_message, parse_mode='Markdown')
        
        async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """معالج أمر /status"""
            status_message = f"""
📊 **حالة البوت الحالية:**

🟢 **الحالة:** نشط وقيد التشغيل
👥 **المستخدمون:** {bot_status['user_count']}
📨 **آخر رسالة:** {bot_status['last_message']['user'] if bot_status['last_message'] else 'لا توجد'}

🌐 **معلومات الخادم:**
• الوضع: {'Webhook' if WEBHOOK_URL else 'Polling'}
• الرابط: {WEBHOOK_URL or 'Polling Mode'}

🔄 **آخر 3 رسائل:**
{chr(10).join([f'• {msg["user"]}: {msg["text"]}' for msg in recent_messages[-3:]]) or 'لا توجد رسائل'}

⚙️ **لاختبار API:** انتقل إلى /health
"""
            await update.message.reply_text(status_message, parse_mode='Markdown')
        
        telegram_app.add_handler(CommandHandler("start", start_command))
        telegram_app.add_handler(CommandHandler("status", status_command))
        
        print("✅ تم إعداد معالجات رسائل التلقرام")
        
    except Exception as e:
        print(f"❌ خطأ في إعداد المعالجات: {e}")

def run_telegram_bot():
    """تشغيل بوت التلقرام"""
    global bot_status
    
    try:
        print("🤖 محاولة تشغيل بوت التلقرام...")
        
        # التحقق من وجود التوكن
        if not BOT_TOKEN or BOT_TOKEN == "your_telegram_bot_token_here":
            print("❌ لم يتم تعيين BOT_TOKEN")
            print("💡 الرجاء تعيين متغير البيئة BOT_TOKEN على Render")
            return
        
        print(f"✅ تم العثور على BOT_TOKEN: {BOT_TOKEN[:10]}...")
        
        # إعداد المعالجات
        setup_telegram_handlers()
        
        # تحديث حالة البوت
        bot_status["is_running"] = True
        
        print("✅ بدأ تشغيل بوت التلقرام في وضع Polling")
        print("💡 جرب إرسال /start إلى بوتك على Telegram")
        
        # تشغيل البوت
        telegram_app.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        
    except Exception as e:
        bot_status["is_running"] = False
        print(f"❌ فشل تشغيل بوت التلقرام: {e}")

# ==================== Flask Routes ====================

@app.route('/')
def home():
    """الصفحة الرئيسية"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Telegram Bot Tester</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                min-height: 100vh;
            }
            .container {
                background: rgba(255, 255, 255, 0.1);
                padding: 30px;
                border-radius: 15px;
                backdrop-filter: blur(10px);
            }
            h1 {
                color: white;
                text-align: center;
            }
            .status-card {
                background: rgba(255, 255, 255, 0.2);
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
            }
            .status-badge {
                display: inline-block;
                padding: 5px 15px;
                border-radius: 20px;
                font-weight: bold;
                margin: 5px;
            }
            .active { background: #4CAF50; }
            .inactive { background: #f44336; }
            .endpoint {
                background: rgba(0, 0, 0, 0.3);
                padding: 15px;
                border-radius: 8px;
                margin: 10px 0;
                font-family: monospace;
            }
            a {
                color: #ffeb3b;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Telegram Bot Tester</h1>
            
            <div class="status-card">
                <h2>📊 حالة النظام</h2>
                <p>البوت: 
                    <span class="status-badge {'active' if bot_status['is_running'] else 'inactive'}">
                        {'🟢 نشط' if bot_status['is_running'] else '🔴 غير نشط'}
                    </span>
                </p>
                <p>عدد المستخدمين: <strong>{bot_status['user_count']}</strong></p>
                <p>آخر رسالة: <strong>{bot_status['last_message']['user'] if bot_status['last_message'] else 'لا توجد'}</strong></p>
            </div>
            
            <div class="status-card">
                <h2>🔗 نقاط الوصول (Endpoints)</h2>
                <div class="endpoint">
                    GET <a href="/health">/health</a> - فحص صحة الخادم
                </div>
                <div class="endpoint">
                    GET <a href="/bot-status">/bot-status</a> - حالة البوت التفصيلية
                </div>
                <div class="endpoint">
                    GET <a href="/recent-messages">/recent-messages</a> - آخر الرسائل
                </div>
                <div class="endpoint">
                    GET <a href="/test-bot">/test-bot</a> - اختبار الاتصال بالبوت
                </div>
            </div>
            
            <div class="status-card">
                <h2>📋 تعليمات التشغيل</h2>
                <ol>
                    <li>تأكد من تعيين متغير البيئة <code>BOT_TOKEN</code> على Render</li>
                    <li>انتقل إلى بوتك على Telegram</li>
                    <li>أرسل <code>/start</code> لتفعيل البوت</li>
                    <li>أرسل أي رسالة نصية وسيتم الرد عليك</li>
                    <li>تحقق من حالة البوت عبر الصفحة الحالية</li>
                </ol>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/health')
def health_check():
    """فحص صحة الخادم"""
    return jsonify({
        'status': 'healthy',
        'service': 'Telegram Bot Tester',
        'bot_running': bot_status['is_running'],
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/bot-status')
def get_bot_status():
    """الحصول على حالة البوت التفصيلية"""
    return jsonify({
        'telegram_bot': {
            'is_running': bot_status['is_running'],
            'token_set': bool(BOT_TOKEN and BOT_TOKEN != "your_telegram_bot_token_here"),
            'webhook_url': WEBHOOK_URL,
            'user_count': bot_status['user_count'],
            'last_message': bot_status['last_message']
        },
        'flask_app': {
            'status': 'running',
            'endpoints': ['/', '/health', '/bot-status', '/recent-messages', '/test-bot']
        },
        'system': {
            'timestamp': datetime.datetime.now().isoformat(),
            'environment': os.getenv('FLASK_ENV', 'production')
        }
    })

@app.route('/recent-messages')
def get_recent_messages():
    """الحصول على آخر الرسائل"""
    return jsonify({
        'count': len(recent_messages),
        'messages': recent_messages,
        'max_stored': 10
    })

@app.route('/test-bot')
def test_bot_connection():
    """اختبار اتصال البوت"""
    try:
        # محاولة الحصول على معلومات البوت
        import asyncio
        
        async def get_bot_info():
            bot = await telegram_app.bot.get_me()
            return {
                'username': bot.username,
                'first_name': bot.first_name,
                'id': bot.id
            }
        
        # تشغيل في loop منفصل
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        bot_info = loop.run_until_complete(get_bot_info())
        loop.close()
        
        return jsonify({
            'success': True,
            'message': '✅ البوت متصل ويعمل',
            'bot_info': bot_info,
            'status': bot_status
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': '❌ البوت غير متصل',
            'error': str(e),
            'status': bot_status
        }), 500

def check_bot_token():
    """التحقق من صحة توكن البوت"""
    if not BOT_TOKEN:
        print("❌ خطأ: لم يتم تعيين BOT_TOKEN")
        print("💡 الرجاء إضافة متغير البيئة BOT_TOKEN على Render:")
        print("   1. انتقل إلى Dashboard Render")
        print("   2. اختر مشروعك")
        print("   3) انتقل إلى Environment")
        print("   4. أضف BOT_TOKEN مع قيمة التوكن من @BotFather")
        return False
    
    if BOT_TOKEN == "your_telegram_bot_token_here":
        print("⚠️ تحذير: BOT_TOKEN ليس حقيقياً")
        print("💡 الرجاء تعيين التوكن الحقيقي من @BotFather")
        return False
    
    # التحقق من صحة شكل التوكن
    if ":" not in BOT_TOKEN:
        print("❌ خطأ: شكل BOT_TOKEN غير صحيح")
        print("💡 التوكن الصحيح يبدو مثل: 1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ")
        return False
    
    return True

if __name__ == '__main__':
    import datetime
    
    print("=" * 50)
    print("🚀 بدء تشغيل Telegram Bot Tester")
    print("=" * 50)
    
    # التحقق من التوكن
    if check_bot_token():
        # تشغيل بوت التلقرام في thread منفصل
        telegram_thread = threading.Thread(target=run_telegram_bot, daemon=True)
        telegram_thread.start()
        print("✅ تم بدء thread بوت التلقرام")
    else:
        print("⚠️ سيتم تشغيل التطبيق بدون بوت التلقرام")
    
    # تشغيل تطبيق Flask
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0'
    
    print(f"🌐 تشغيل تطبيق Flask على {host}:{port}")
    print(f"📊 لوحة التحكم: http://localhost:{port}" if port != 5000 else "📊 لوحة التحكم: http://localhost:5000")
    print("=" * 50)
    
    app.run(host=host, port=port, debug=False, use_reloader=False)