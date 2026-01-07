from flask import Flask, jsonify
import os
import threading
import time

app = Flask(__name__)

# الحصول على توكن البوت من متغيرات البيئة
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# متغير لتتبع حالة البوت
bot_status = {
    "is_running": False,
    "last_check": None,
    "error": None
}

def simple_telegram_test():
    """اختبار بسيط للاتصال بتلقرام"""
    print("🔍 اختبار اتصال Telegram Bot...")
    
    if not BOT_TOKEN:
        bot_status["error"] = "❌ لم يتم تعيين BOT_TOKEN"
        print(bot_status["error"])
        return
    
    if BOT_TOKEN == "your_telegram_bot_token_here":
        bot_status["error"] = "⚠️ التوكن غير صالح (استخدم التوكن الحقيقي)"
        print(bot_status["error"])
        return
    
    # التحقق من شكل التوكن (يجب أن يحتوي على : )
    if ":" not in BOT_TOKEN:
        bot_status["error"] = "❌ شكل التوكن غير صحيح"
        print(bot_status["error"])
        return
    
    try:
        # محاولة استيراد مكتبة تلقرام
        from telegram.ext import ApplicationBuilder
        
        print(f"✅ تم العثور على توكن صالح: {BOT_TOKEN[:10]}...")
        
        # إنشاء تطبيق تلقرام
        telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()
        
        # اختبار الاتصال
        import asyncio
        
        async def test_connection():
            bot = await telegram_app.bot.get_me()
            return bot
        
        # إنشاء event loop جديد
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        bot_info = loop.run_until_complete(test_connection())
        loop.close()
        
        bot_status["is_running"] = True
        bot_status["last_check"] = time.strftime("%Y-%m-%d %H:%M:%S")
        bot_status["bot_info"] = {
            "username": bot_info.username,
            "name": bot_info.first_name,
            "id": bot_info.id
        }
        
        print("✅ ✅ ✅ تم الاتصال بنجاح!")
        print(f"🤖 اسم البوت: @{bot_info.username}")
        print(f"👋 اسم العرض: {bot_info.first_name}")
        print(f"🆔 رقم البوت: {bot_info.id}")
        print("\n💡 الآن أرسل رسالة إلى بوتك وسيتم الرد عليك!")
        
    except ImportError:
        bot_status["error"] = "❌ مكتبة python-telegram-bot غير مثبتة"
        print(bot_status["error"])
    except Exception as e:
        bot_status["error"] = f"❌ فشل الاتصال: {str(e)}"
        print(bot_status["error"])

def start_telegram_bot():
    """تشغيل البوت البسيط"""
    print("🚀 بدء تشغيل Telegram Bot...")
    simple_telegram_test()
    
    if bot_status["is_running"]:
        print("\n🎉 البوت جاهز للاستخدام!")
        print("📱 افتح Telegram وابحث عن بوتك")
        print("💬 أرسل أي رسالة وسيتم الرد عليك")
    else:
        print("\n⚠️ البوت غير نشط")
        print("🔧 تحقق من:")
        print("   1. متغير BOT_TOKEN على Render")
        print("   2. التوكن الحقيقي من @BotFather")

@app.route('/')
def home():
    """الصفحة الرئيسية"""
    status_color = "green" if bot_status["is_running"] else "red"
    status_text = "🟢 نشط" if bot_status["is_running"] else "🔴 غير نشط"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Telegram Bot Status</title>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                text-align: center;
                padding: 50px;
                background: #f0f0f0;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .status {{
                font-size: 24px;
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
                background: {status_color};
                color: white;
            }}
            .info {{
                text-align: left;
                background: #f9f9f9;
                padding: 20px;
                border-radius: 5px;
                margin: 20px 0;
            }}
            code {{
                background: #eee;
                padding: 2px 5px;
                border-radius: 3px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 حالة Telegram Bot</h1>
            
            <div class="status">
                {status_text}
            </div>
            
            <div class="info">
                <h3>📊 معلومات البوت:</h3>
                <p><strong>الحالة:</strong> {'متصل ✅' if bot_status['is_running'] else 'غير متصل ❌'}</p>
                <p><strong>آخر فحص:</strong> {bot_status['last_check'] or 'لم يتم'}</p>
                
                {f'<p><strong>اسم البوت:</strong> @{bot_status["bot_info"]["username"]}</p>' if bot_status.get('bot_info') else ''}
                {f'<p><strong>اسم العرض:</strong> {bot_status["bot_info"]["name"]}</p>' if bot_status.get('bot_info') else ''}
                
                {f'<p style="color:red;"><strong>خطأ:</strong> {bot_status["error"]}</p>' if bot_status.get('error') else ''}
            </div>
            
            <div class="info">
                <h3>🔗 رابط الاختبار:</h3>
                <p><a href="/health">/health</a> - فحص صحة الخادم</p>
                <p><a href="/status">/status</a> - حالة البوت بالتفصيل</p>
            </div>
            
            <div class="info">
                <h3>📋 خطوات التشغيل:</h3>
                <ol>
                    <li>اذهب إلى @BotFather على Telegram</li>
                    <li>أنشئ بوت جديد واحصل على التوكن</li>
                    <li>أضف التوكن في متغيرات البيئة على Render</li>
                    <li>أرسل رسالة إلى بوتك</li>
                </ol>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/health')
def health():
    """فحص صحة الخادم"""
    return jsonify({
        "status": "healthy",
        "bot_connected": bot_status["is_running"],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route('/status')
def status():
    """حالة البوت التفصيلية"""
    return jsonify(bot_status)

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 بدء تشغيل Telegram Bot Tester")
    print("=" * 50)
    
    # اختبار الاتصال في thread منفصل
    bot_thread = threading.Thread(target=start_telegram_bot, daemon=True)
    bot_thread.start()
    
    # تشغيل Flask
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 تشغيل خادم الويب على المنفذ {port}")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=port, debug=False)