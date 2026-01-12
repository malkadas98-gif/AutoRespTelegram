from datetime import datetime
from intent_analyzer import IntentAnalyzer
from nlp_engine import FlightNLP
from flight_system import flight_system
from flask import Flask, app, request, jsonify, render_template, redirect, url_for, flash
# ===========================
# المحللات
# ===========================
intent_analyzer = IntentAnalyzer()
nlp_engine = FlightNLP()


# ===========================
# الدالة الرئيسية
# ===========================
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
                
                # استخدام الدالة المعدلة للحصول على الرد
                response = flight_system.get_cheapest_flight_response(query, formatted_results)
                
                # تسجيل البحث في التاريخ
                if user_id:
                    flights_found = formatted_results.get('count', 0)
                    # log_search_history(user_id, user_text, nlp_result, True, flights_found)
                
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
