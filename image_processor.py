from PIL import Image, ImageEnhance
import pytesseract
import io
import requests
import re
import difflib
from datetime import datetime

# ---------------------------------------------------
# 1) قائمة رموز مطارات IATA (أضفت مجموعة كبيرة)
# ---------------------------------------------------

IATA_AIRPORTS = {
    "CAI","JFK","DOH","MCT","CAN","DXB","AUH","LHR","CDG","FRA","IST","AMS",
    "JED","RUH","HBE","SSH","KWI","BKK","SIN","LAX","ORD","MUC","ATH","MAD",
    "BCN","KUL","NRT","HND","ICN","DOH","ADD","CMN","TIP","ALG","TUN","DAR",
    "KHI","DEL","BOM","MLE","JNB","CPT","SYD","MEL","BNE","SFO","SEA","YYZ",
    "YVR","ORD","IAD","DCA","MIA","DFW","PHX"
}

# ---------------------------------------------------
# دالة لتصحيح رموز المطارات لو تم تشويهها عبر OCR
# ---------------------------------------------------
def fix_airport_code(code):
    """إصلاح رموز المطارات المشوهة بواسطة OCR"""
    
    # إذا كان الرمز الصحيح موجود مباشرة
    if code in IATA_AIRPORTS:
        return code
    
    # مثلاً CAT → CAI
    close = difflib.get_close_matches(code, IATA_AIRPORTS, n=1, cutoff=0.55)
    if close:
        return close[0]
    
    return code


# ===================================================
#              ✈ كلاس معالجة صور الطيران
# ===================================================
class FlightImageProcessor:
    def __init__(self, telegram_app):
        self.telegram_app = telegram_app
    
    # ------------------------------------------------
    # تحسين الصورة لـ OCR
    # ------------------------------------------------
    def preprocess_image(self, image):
        try:
            image = ImageEnhance.Contrast(image).enhance(2.0)
            image = ImageEnhance.Sharpness(image).enhance(2.0)
            image = image.convert("L")
            return image
        except:
            return image

    # ------------------------------------------------
    # استخراج النص من الصورة
    # ------------------------------------------------
    async def extract_text_from_image(self, image_data):
        try:
            image = Image.open(io.BytesIO(image_data))
            image = self.preprocess_image(image)

            config = r'--oem 3 --psm 6 -l eng'
            text = pytesseract.image_to_string(image, config=config)

            return text
        except:
            return None

    # ------------------------------------------------
    # تحميل الصورة من تليغرام
    # ------------------------------------------------
    async def download_telegram_image(self, file_id):
        try:
            file = await self.telegram_app.bot.get_file(file_id)
            response = requests.get(file.file_path)

            return response.content if response.status_code == 200 else None
        except:
            return None

    # ------------------------------------------------
    # تحليل بيانات التذكرة من النص
    # ------------------------------------------------
    def parse_flight_info_from_image(self, text):

        # تنظيف النص
        cleaned = [l.strip() for l in text.split("\n") if l.strip()]

        # ------------------------------------------------
        # 1) استخراج كل الرموز المكونة من 3 أحرف أو شبه 3
        # ------------------------------------------------
        raw_airports = re.findall(r"[A-Z][A-Z0-9]{2}", text)

        # إصلاح الرموز المشوهة
        airports = []
        for code in raw_airports:
            fixed = fix_airport_code(code)
            if fixed in IATA_AIRPORTS and fixed not in airports:
                airports.append(fixed)

        # تحديد الانطلاق والوصول
        origin = airports[0] if len(airports) >= 1 else ""
        destination = airports[-1] if len(airports) >= 2 else ""

        # ------------------------------------------------
        # 2) استخراج التاريخ بكل الصيغ الممكنة
        # ------------------------------------------------
        date_patterns = [
            r'\b(\d{1,2}[A-Z]{3})\b',               # 27NOV
            r'\b(\d{1,2}\s?[A-Z]{3})\b',            # 27 NOV
            r'\b(\d{1,2}\s[A-Za-z]{3,9}\s?\d{2,4})\b',  # 27 November 2025
            r'\b([A-Z]{3}\s\d{1,2})\b',            # OCT 23
        ]

        date_found = None
        for pattern in date_patterns:
            m = re.search(pattern, text)
            if m:
                date_found = m.group(1)
                break

        # تحويل التاريخ إلى صيغة 25 NOV
        if date_found:
            date_fixed = date_found.replace("  ", " ").strip()

            try:
                # عدة احتمالات للفك
                for fmt in ("%d%b", "%d %b", "%d %B %Y", "%b %d"):
                    try:
                        dt = datetime.strptime(date_fixed.replace(" ", ""), fmt)
                        date_fixed = dt.strftime("%d %b")
                        break
                    except:
                        pass
            except:
                pass
        else:
            date_fixed = ""

        # ------------------------------------------------
        # 3) استخراج رقم الرحلة (لو احتاجه النظام لاحقاً)
        # ------------------------------------------------
        flight_numbers = re.findall(r"\b[A-Z]{1,2}\s?\d{2,4}\b", text)

        # ------------------------------------------------
        # 4) إعداد النتيجة النهائية
        # ------------------------------------------------
        success = bool(origin and destination and date_fixed)

        return {
            "origin": origin,
            "destination": destination,
            "date": date_fixed,
            "flight_numbers": flight_numbers,
            "all_airports_detected": airports,
            "success": success,
            "search_query": f"{origin} {destination} {date_fixed}" if success else "",
            "raw_text": text
        }

    # ------------------------------------------------
    # إنشاء استعلام البحث
    # ------------------------------------------------
    def create_search_query(self, flight_info):
        if not flight_info["success"]:
            return None
        return f"{flight_info['origin']} {flight_info['destination']} {flight_info['date']}"
