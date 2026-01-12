from datetime import datetime
from intent_analyzer import IntentAnalyzer
from nlp_engine import FlightNLP
from flight_system import flight_system

# إنشاء المحللات مرة واحدة
intent_analyzer = IntentAnalyzer()
nlp_engine = FlightNLP()

async def process_flight_query(user_text, user_id=None):
    """
    يعالج استعلام المستخدم ويُرجع:
    - نص واحد
    - أو قائمة رسائل (نتائج رحلات)
    """

    try:
        # 1️⃣ تحليل النية
        intent_result = intent_analyzer.analyze_intent(user_text)

        if intent_result["intent"] in ["gibberish"]:
            return intent_result["response"]

        if intent_result["intent"] in [
            "greeting", "thanks", "general_question", "help", "unclear"
        ]:
            return intent_result["response"]

        # 2️⃣ تحليل NLP
        nlp_result = nlp_engine.process_query(user_text)

        if not nlp_result.get("success"):
            missing = nlp_result.get("missing_info", [])
            if missing:
                return (
                    "✈️ أحتاج معلومات إضافية:\n"
                    f"📋 {', '.join(missing)}\n\n"
                    "مثال:\n"
                    "رحلة من الرياض إلى دبي يوم 20 يناير لشخصين"
                )
            return "❌ لم أستطع فهم تفاصيل الرحلة"

        query = nlp_result["query"]

        # 3️⃣ البحث عن الرحلات
        search_result = flight_system.search_flights_safe(
            query["origin"],
            query["destination"],
            query["date"],
            query["adults"]
        )

        formatted = flight_system.format_flight_results(search_result)

        if formatted.get("count", 0) == 0:
            return "❌ لم يتم العثور على رحلات متاحة في هذا التاريخ"

        # 4️⃣ بناء الرد (عدة نتائج)
        messages = []

        header = (
            f"✈️ **نتائج الرحلات**\n\n"
            f"📍 من: {query['origin']}\n"
            f"📍 إلى: {query['destination']}\n"
            f"📅 التاريخ: {query['date']}\n"
            f"👤 الركاب: {query['adults']}\n\n"
            f"🔍 عدد الرحلات: {formatted['count']}\n"
            "----------------------"
        )
        messages.append(header)

        for idx, flight in enumerate(formatted["flights"][:5], start=1):
            msg = (
                f"✈️ **رحلة {idx}**\n"
                f"🏢 شركة الطيران: {flight['airline']}\n"
                f"🕒 الإقلاع: {flight['departure_time']}\n"
                f"🕓 الوصول: {flight['arrival_time']}\n"
                f"⏱️ المدة: {flight['duration']}\n"
                f"💺 التوقفات: {flight['stops']}\n"
                f"💰 السعر: {flight['price']} {flight['currency']}\n"
                "----------------------"
            )
            messages.append(msg)

        return messages

    except Exception as e:
        print(f"❌ Core Logic Error: {e}")
        return "❌ حدث خطأ أثناء البحث عن الرحلات"
