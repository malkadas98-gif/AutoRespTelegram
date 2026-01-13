from datetime import datetime
from intent_analyzer import IntentAnalyzer
from nlp_engine import FlightNLP
from flight_system import flight_system

# ===========================
# المحللات
# ===========================
intent_analyzer = IntentAnalyzer()
nlp_engine = FlightNLP()

# ===========================
# اختصارات المدن
# ===========================
CITY_ALIASES = {
    "Jed": "Jeddah",
    "Ist": "Istanbul",
    "Cai": "Cairo",
    "Riy": "Riyadh",
    "Dub": "Dubai"
}

# ===========================
# دالة لتحويل اسم المدينة
# ===========================
def normalize_city(city_name):
    return CITY_ALIASES.get(city_name.strip(), city_name.strip())

# ===========================
# دالة لتحويل التواريخ
# ===========================
def parse_date(date_str):
    """
    يحول تواريخ قصيرة مثل 20Jan أو 20-01-2026 إلى YYYY-MM-DD
    يدعم العربية والإنجليزية
    """
    date_str = date_str.strip()
    try:
        # تجربة ISO
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except:
        pass
    try:
        # تجربة DD-MM-YYYY
        dt = datetime.strptime(date_str, "%d-%m-%Y")
        return dt.strftime("%Y-%m-%d")
    except:
        pass
    try:
        # تجربة English short month, مثل 20Jan
        dt = datetime.strptime(date_str, "%d%b")
        # افترض السنة الحالية
        dt = dt.replace(year=datetime.now().year)
        return dt.strftime("%Y-%m-%d")
    except:
        pass
    try:
        # تجربة Arabic: 20 يناير
        arabic_months = {
            "يناير":1, "فبراير":2, "مارس":3, "أبريل":4, "مايو":5, "يونيو":6,
            "يوليو":7, "أغسطس":8, "سبتمبر":9, "أكتوبر":10, "نوفمبر":11, "ديسمبر":12
        }
        parts = date_str.split()
        if len(parts)==2:
            day = int(parts[0])
            month = arabic_months.get(parts[1])
            if month:
                dt = datetime(datetime.now().year, month, day)
                return dt.strftime("%Y-%m-%d")
    except:
        pass
    # إذا فشل التحويل
    return None

# ===========================
# الدالة الرئيسية
# ===========================
async def process_flight_query(user_text, user_id=None):
    """
    يعالج استعلام المستخدم ويُرجع قائمة النتائج
    """
    try:
        # ===== تحليل النية =====
        intent_result = intent_analyzer.analyze_intent(user_text)

        if intent_result["intent"] in ["gibberish"]:
            return intent_result["response"]

        if intent_result["intent"] in [
            "greeting", "thanks", "general_question", "help", "unclear"
        ]:
            return intent_result["response"]

        # ===== NLP =====
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

        # ===== تصحيح المدن والتاريخ =====
        query["origin"] = normalize_city(query["origin"])
        query["destination"] = normalize_city(query["destination"])
        date_parsed = parse_date(query["date"])
        if date_parsed:
            query["date"] = date_parsed
        else:
            return "❌ لم أتمكن من فهم تاريخ الرحلة"

        # ===== البحث عن الرحلات =====
        search_result = flight_system.search_flights_safe(
            query["origin"],
            query["destination"],
            query["date"],
            query["adults"]
        )

        formatted = flight_system.format_flight_results(search_result)

        if formatted.get("count", 0) == 0:
            return "❌ لم يتم العثور على رحلات متاحة في هذا التاريخ"

        # ===== بناء الرد (أفضل 5 رحلات) =====
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
