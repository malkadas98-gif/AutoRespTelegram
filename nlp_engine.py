import re
from datetime import datetime, timedelta
from models import db, City, Month, ArabicTextReplacement, Airline, Country

class FlightNLP:
    def __init__(self, app=None):
        self.app = app
        self.setup_data()
    
    def init_app(self, app):
        """تهيئة التطبيق مع NLP"""
        self.app = app
        self.setup_data()
    
    def setup_data(self):
        """إعداد البيانات من قاعدة البيانات"""
        self.load_cities_from_db()
        self.load_months_from_db()
        self.load_text_replacements_from_db()
        self.load_airlines_from_db()
        self.setup_english_months()
    
    def setup_english_months(self):
        """إعداد الأشهر الإنجليزية"""
        self.english_months = [
            'January','February','March','April','May','June',
            'July','August','September','October','November','December'
        ]
        self.english_months_abbr = [
            'Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'
        ]
        self.english_months_dict = {
            'January': '01','Jan': '01',
            'February': '02','Feb': '02',
            'March': '03','Mar': '03',
            'April': '04','Apr': '04',
            'May': '05','June': '06','Jun': '06',
            'July': '07','Jul': '07',
            'August': '08','Aug': '08',
            'September': '09','Sep': '09',
            'October': '10','Oct': '10',
            'November': '11','Nov': '11',
            'December': '12','Dec': '12'
        }

    # ✅ دالة المدن الموحدة
    def load_cities_from_db(self):
        """تحميل المدن من قاعدة البيانات فقط"""
        try:
            if self.app:
                with self.app.app_context():
                    cities_db = City.query.filter_by(is_active=True).all()

                    if not cities_db:
                        print("⚠️ لا توجد مدن في قاعدة البيانات. يرجى إضافة بيانات في جدول cities.")
                        self.arabic_cities = {}
                        self.english_cities = {}
                        self.city_codes = {}
                        return

                    self.arabic_cities = {c.arabic_name: c.iata_code for c in cities_db}
                    self.english_cities = {c.english_name.lower(): c.iata_code for c in cities_db}
                    self.city_codes = {c.iata_code: c.iata_code for c in cities_db}
                    
                    print(f"✅ تم تحميل {len(cities_db)} مدينة من قاعدة البيانات")
            else:
                print("⚠️ لم يتم تمرير التطبيق إلى NLP.")
                #self.setup_default_cities()
        except Exception as e:
            print(f"❌ خطأ في تحميل المدن من قاعدة البيانات: {e}")
            #self.setup_default_cities()
    
    def load_months_from_db(self):
        """تحميل الأشهر من قاعدة البيانات"""
        try:
            if self.app:
                with self.app.app_context():
                    months_db = Month.query.filter_by(is_active=True).all()
                    self.months = {month.arabic_name: str(month.month_number).zfill(2) for month in months_db}
                    print(f"✅ تم تحميل {len(months_db)} شهر من قاعدة البيانات")
            else:
                self.setup_default_months()
                
        except Exception as e:
            print(f"❌ خطأ في تحميل الأشهر من قاعدة البيانات: {e}")
            self.setup_default_months()
    
    def load_text_replacements_from_db(self):
        """تحميل استبدالات النص من قاعدة البيانات"""
        try:
            if self.app:
                with self.app.app_context():
                    replacements_db = ArabicTextReplacement.query.filter_by(is_active=True).all()
                    self.text_replacements = {rep.original_text: rep.replacement_text for rep in replacements_db}
                    print(f"✅ تم تحميل {len(replacements_db)} استبدال نصي من قاعدة البيانات")
            else:
                self.setup_default_replacements()
                
        except Exception as e:
            print(f"❌ خطأ في تحميل استبدالات النص من قاعدة البيانات: {e}")
            self.setup_default_replacements()

    def load_airlines_from_db(self):
        """تحميل شركات الطيران من قاعدة البيانات"""
        try:
            if self.app:
                with self.app.app_context():
                    airlines_db = Airline.query.filter_by(is_active=True).all()
                    self.airlines = {
                        'by_iata': {airline.iata_code: {
                            'arabic_name': airline.arabic_name,
                            'english_name': airline.english_name,
                            'icao': airline.icao_code,
                            'country': airline.country.arabic_name if airline.country else 'غير معروف'
                        } for airline in airlines_db},
                        'by_arabic': {airline.arabic_name: airline.iata_code for airline in airlines_db},
                        'by_english': {airline.english_name.lower(): airline.iata_code for airline in airlines_db}
                    }
                    print(f"✅ تم تحميل {len(airlines_db)} شركة طيران من قاعدة البيانات")
            else:
                 print(f"❌ خطأ في تحميل شركات الطيران من قاعدة البيانات: ")
                
        except Exception as e:
            print(f"❌ خطأ في تحميل شركات الطيران من قاعدة البيانات: {e}")
            
    
    
    def setup_default_months(self):
        """إعداد الأشهر الافتراضية"""
        self.months = {
            'يناير': '01', 'فبراير': '02', 'مارس': '03',
            'ابريل': '04', 'مايو': '05', 'يونيو': '06',
            'يوليو': '07', 'اغسطس': '08', 'سبتمبر': '09',
            'اكتوبر': '10', 'نوفمبر': '11', 'ديسمبر': '12'
        }
        print("⚠️ استخدام الأشهر الافتراضية (لم يتم تحميلها من قاعدة البيانات)")
    
    def setup_default_replacements(self):
        """إعداد استبدالات النص الافتراضية"""
        self.text_replacements = {
            'إلى': 'الى', 'أ': 'ا', 'إ': 'ا', 'آ': 'ا',
            'ة': 'ه', 'ـ': '', 'ّ': '', 'َ': '', 'ُ': '', 'ِ': '', 'ْ': '',
            'غدا': 'غدا', 'بكرا': 'غدا', 'غداً': 'غدا', 'بكراً': 'غدا',
            'رحلة': '', 'رحله': '', 'طيران': '', 'تذكرة': '', 'تذاكر': '',
            'يوم': '', 'تاريخ': '', 'بتاريخ': '', 'في': ''
        }
        print("⚠️ استخدام استبدالات النص الافتراضية (لم يتم تحميلها من قاعدة البيانات)")

   
    def refresh_data(self):
        """تحديث البيانات من قاعدة البيانات"""
        print("🔄 تحديث البيانات من قاعدة البيانات...")
        self.load_cities_from_db()
        self.load_months_from_db()
        self.load_text_replacements_from_db()
        self.load_airlines_from_db()

    def normalize_arabic_text(self, text):
        """توحيد النص العربي باستخدام استبدالات قاعدة البيانات فقط"""
        if not text:
            return ""
            
        text = str(text)
        
        # استبدالات من قاعدة البيانات
        if hasattr(self, "text_replacements") and self.text_replacements:
            if isinstance(self.text_replacements, dict):
                for old, new in self.text_replacements.items():
                    text = text.replace(old, new)
        
        return text.lower()

    def clean_text(self, text):
        """تنظيف النص"""
        if not text:
            return ""
            
        text = str(text)
        text = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def extract_cities(self, text):
        """استخراج المدن (العربية والإنجليزية) بذكاء حتى في حال التصاق الكلمات أو الأسطر المتعددة"""
        normalized_text = self.normalize_arabic_text(text)
        found_cities = []
        
        # دمج كل المدن في قاموس واحد
        all_cities = {**self.arabic_cities, **self.english_cities, **self.city_codes}
        
        # 🔹 نقسم النص إلى كلمات منفصلة (تراعي الأسطر والمسافات)
        tokens = re.split(r'[\s\n]+', normalized_text)
        cleaned_tokens = [t.strip() for t in tokens if len(t.strip()) > 1]

        # 🔹 البحث عن المدن داخل الكلمات
        for token in cleaned_tokens:
            for city_name, city_code in all_cities.items():
                norm_city = self.normalize_arabic_text(city_name)
                if norm_city and norm_city in token:
                    # تجنب التكرار
                    if not any(c['code'] == city_code for c in found_cities):
                        found_cities.append({
                            'name': city_name,
                            'code': city_code,
                            'type': 'unknown'
                        })

        # 🔹 ترتيب المدن بناءً على موقعها في النص
        found_cities = sorted(
            found_cities,
            key=lambda c: normalized_text.find(self.normalize_arabic_text(c['name']))
        )

        # 🔹 تحديد الاتجاه (من → إلى)
        if len(found_cities) >= 2:
            found_cities[0]['type'] = 'origin'
            found_cities[1]['type'] = 'destination'
        elif len(found_cities) == 1:
            found_cities[0]['type'] = 'unknown'

        # 🔹 دعم الحالات التي تحتوي على أكثر من مدينتين (مثل الترانزيت)
        # نكتفي فقط بأول مدينتين كبداية ونهاية
        return found_cities[:2]

    def detect_city_type(self, city, text):
        """تحديد نوع المدينة"""
        city_norm = self.normalize_arabic_text(city)
        index = text.find(city_norm)
        
        if index > 0:
            preceding = text[:index].strip()
            words = preceding.split()[-3:]
            
            for word in words:
                if word in ['من', 'مغادرة']:
                    return 'origin'
                elif word in ['الى', 'ل', 'وصول', 'الي']:
                    return 'destination'
        
        return 'unknown'

    def extract_dates(self, text):
        """استخراج جميع صيغ التواريخ المحتملة"""
        normalized_text = self.normalize_arabic_text(text)
        dates = []
        current_year = datetime.now().year

        # الأنماط الرقمية والقياسية
        pattern1 = r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})'
        for year, month, day in re.findall(pattern1, text):
            dates.append({'day': int(day), 'month': int(month), 'year': int(year)})

        pattern2 = r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})'
        for day, month, year in re.findall(pattern2, normalized_text):
            dates.append({'day': int(day), 'month': int(month), 'year': int(year)})

        # تواريخ عربية وإنجليزية مع وبدون سنة
        pattern3 = r'(\d{1,2})\s*(' + '|'.join(self.months.keys()) + r')\s*(\d{4})'
        for day, month_ar, year in re.findall(pattern3, normalized_text):
            month_num = self.months.get(month_ar, '01')
            dates.append({'day': int(day), 'month': int(month_num), 'year': int(year)})

        pattern4 = r'(\d{1,2})\s*(' + '|'.join(self.months.keys()) + r')'
        for day, month_ar in re.findall(pattern4, normalized_text):
            month_num = self.months.get(month_ar, '01')
            dates.append({'day': int(day), 'month': int(month_num), 'year': current_year})

        pattern5 = r'(' + '|'.join(self.english_months + self.english_months_abbr) + r')\s*(\d{1,2}),?\s*(\d{2,4})'
        for month_en, day, year in re.findall(pattern5, text, re.IGNORECASE):
            if len(year) == 2:
                year = f"20{year}"
            month_num = self.english_months_dict.get(month_en.title(), '01')
            dates.append({'day': int(day), 'month': int(month_num), 'year': int(year)})

        pattern6 = r'(\d{1,2})\s*(' + '|'.join(self.english_months + self.english_months_abbr) + r'),?\s*(\d{2,4})'
        for day, month_en, year in re.findall(pattern6, text, re.IGNORECASE):
            if len(year) == 2:
                year = f"20{year}"
            month_num = self.english_months_dict.get(month_en.title(), '01')
            dates.append({'day': int(day), 'month': int(month_num), 'year': int(year)})

        pattern7 = r'(' + '|'.join(self.english_months + self.english_months_abbr) + r')\s*(\d{1,2})'
        for month_en, day in re.findall(pattern7, text, re.IGNORECASE):
            month_num = self.english_months_dict.get(month_en.title(), '01')
            dates.append({'day': int(day), 'month': int(month_num), 'year': current_year})

        pattern8 = r'(\d{1,2})\s*(' + '|'.join(self.english_months + self.english_months_abbr) + r')'
        for day, month_en in re.findall(pattern8, text, re.IGNORECASE):
            month_num = self.english_months_dict.get(month_en.title(), '01')
            dates.append({'day': int(day), 'month': int(month_num), 'year': current_year})

        # بدون مسافات
        compact_pattern1 = r'(\d{1,2})(' + '|'.join(self.english_months + self.english_months_abbr) + r')'
        compact_pattern2 = r'(' + '|'.join(self.english_months + self.english_months_abbr) + r')(\d{1,2})'
        for day, month_en in re.findall(compact_pattern1, text, re.IGNORECASE):
            month_num = self.english_months_dict.get(month_en.title(), '01')
            dates.append({'day': int(day), 'month': int(month_num), 'year': current_year})
        for month_en, day in re.findall(compact_pattern2, text, re.IGNORECASE):
            month_num = self.english_months_dict.get(month_en.title(), '01')
            dates.append({'day': int(day), 'month': int(month_num), 'year': current_year})

        # أنماط عربية خاصة
        pattern12 = r'(?:يوم|تاريخ|في|موعد)\s*(\d{1,2})\s*(' + '|'.join(self.months.keys()) + r')'
        for day, month_ar in re.findall(pattern12, normalized_text):
            month_num = self.months.get(month_ar, '01')
            dates.append({'day': int(day), 'month': int(month_num), 'year': current_year})

        pattern13 = r'(?:يوم|تاريخ|في|موعد)\s*(\d{1,2})\s*(' + '|'.join(self.months.keys()) + r')\s*(?:سنه|سنة)\s*(\d{4})'
        for day, month_ar, year in re.findall(pattern13, normalized_text):
            month_num = self.months.get(month_ar, '01')
            dates.append({'day': int(day), 'month': int(month_num), 'year': int(year)})

        pattern14 = r'(\d{1,2})\s*(' + '|'.join(self.months.keys()) + r')\s*(\d{2,4})?'
        for day, month_ar, year in re.findall(pattern14, normalized_text):
            month_num = self.months.get(month_ar, '01')
            year_val = int(year) if year else current_year
            if year_val < 100:
                year_val += 2000
            dates.append({'day': int(day), 'month': int(month_num), 'year': year_val})

        # التواريخ النسبية
        dates.extend(self.extract_relative_dates(normalized_text))

        # إزالة التكرار
        unique_dates = []
        for d in dates:
            if d not in unique_dates:
                unique_dates.append(d)
        return unique_dates

    # ⏰ التواريخ النسبية
    def extract_relative_dates(self, text):
        text = text.lower().strip()
        today = datetime.now()
        dates = []

        arabic_relative = {
            r'اليوم': 0,
            r'انهارده': 0,
            r'بكره': 1,
            r'بكرا': 1,
            r'غدا': 1,
            r'غداً': 1,
            r'بعد\s*غد': 2,
            r'بعد\s*غداً': 2,
            r'الاسبوع\s*القادم': 7,
            r'الأسبوع\s*القادم': 7,
            r'الشهر\s*القادم': 30,
            r'الشهر\s*التالي': 30,
        }

        english_relative = {
            r'\btoday\b': 0,
            r'\btomorrow\b': 1,
            r'\bthe day after tomorrow\b': 2,
            r'\bnext week\b': 7,
            r'\bnext month\b': 30,
        }

        for pattern, offset in {**arabic_relative, **english_relative}.items():
            if re.search(pattern, text):
                target = today + timedelta(days=offset)
                dates.append({'day': target.day, 'month': target.month, 'year': target.year})

        for match in re.findall(r'بعد\s+(\d+)\s*(?:يوم|ايام|أيام)', text):
            target = today + timedelta(days=int(match))
            dates.append({'day': target.day, 'month': target.month, 'year': target.year})

        for match in re.findall(r'after\s+(\d+)\s*(?:day|days)', text):
            target = today + timedelta(days=int(match))
            dates.append({'day': target.day, 'month': target.month, 'year': target.year})

        for match in re.findall(r'خلال\s+(\d+)\s*(?:يوم|ايام|أيام)', text):
            target = today + timedelta(days=int(match))
            dates.append({'day': target.day, 'month': target.month, 'year': target.year})

        for match in re.findall(r'within\s+(\d+)\s*(?:day|days)', text):
            target = today + timedelta(days=int(match))
            dates.append({'day': target.day, 'month': target.month, 'year': target.year})

        unique_dates = []
        for d in dates:
            if d not in unique_dates:
                unique_dates.append(d)
        return unique_dates
    
    def extract_passengers(self, text):
        """استخراج عدد المسافرين"""
        normalized_text = self.normalize_arabic_text(text)
        passengers = {'adults': 1, 'children': 0, 'infants': 0, 'total': 1}
        
        # البحث عن أنماط رقمية
        patterns = [
            r'لـ?\s*(\d+)\s*(شخص|راكب|بالغ|شخصين|اشخاص)',
            r'(\d+)\s*(شخص|راكب|بالغ|مسافر)',
            r'لـ?\s*(\d+)',
            r'عدد\s*(\d+)',
            r'(\d+)\s+مسافر',
            r'for\s*(\d+)\s*(person|people|passenger|adult)',
            r'(\d+)\s*(person|people|passenger|adult)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, normalized_text)
            if match:
                num = int(match.group(1))
                passengers['adults'] = num
                passengers['total'] = num
                break
        
        # البحث عن كلمات عددية
        word_numbers = {
            'واحد': 1, 'احد': 1, 'شخص واحد': 1,
            'اثنان': 2, 'اثنين': 2, 'شخصين': 2,
            'ثلاثة': 3, 'ثلاثه': 3, 'ثلاث اشخاص': 3,
            'اربعة': 4, 'اربعه': 4, 'اربع اشخاص': 4,
            'خمسة': 5, 'خمسه': 5, 'خمس اشخاص': 5,
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5
        }
        
        for word, num in word_numbers.items():
            if word in normalized_text:
                passengers['adults'] = num
                passengers['total'] = num
                break
        
        return passengers

    def extract_airlines(self, text):
        """استخراج شركات الطيران من النص"""
        normalized_text = self.normalize_arabic_text(text)
        found_airlines = []
        
        # البحث بالأسماء العربية
        for arabic_name, iata_code in self.airlines['by_arabic'].items():
            norm_name = self.normalize_arabic_text(arabic_name)
            if norm_name in normalized_text:
                found_airlines.append({
                    'iata_code': iata_code,
                    'arabic_name': arabic_name,
                    'english_name': self.airlines['by_iata'][iata_code]['english_name'],
                    'type': 'airline'
                })
        
        # البحث بالأسماء الإنجليزية
        for english_name, iata_code in self.airlines['by_english'].items():
            norm_name = english_name.lower()
            if norm_name in normalized_text.lower():
                # تجنب التكرار
                if not any(al['iata_code'] == iata_code for al in found_airlines):
                    found_airlines.append({
                        'iata_code': iata_code,
                        'arabic_name': self.airlines['by_iata'][iata_code]['arabic_name'],
                        'english_name': english_name,
                        'type': 'airline'
                    })
        
        # البحث برموز IATA
        iata_pattern = r'\b([A-Z]{2})\b'
        matches = re.findall(iata_pattern, text.upper())
        for iata_code in matches:
            if iata_code in self.airlines['by_iata'] and not any(al['iata_code'] == iata_code for al in found_airlines):
                airline_info = self.airlines['by_iata'][iata_code]
                found_airlines.append({
                    'iata_code': iata_code,
                    'arabic_name': airline_info['arabic_name'],
                    'english_name': airline_info['english_name'],
                    'type': 'airline'
                })
        
        return found_airlines

    def get_airline_info(self, iata_code):
        """الحصول على معلومات شركة الطيران"""
        airline_info = self.airlines['by_iata'].get(iata_code, {})
        if not airline_info:
            return {
                'arabic_name': 'غير معروف',
                'english_name': 'Unknown',
                'icao': 'N/A',
                'country': 'غير معروف'
            }
        return airline_info

    def process_query(self, user_text):
        """معالجة الاستفسار"""
        try:
            if not user_text or not user_text.strip():
                return {'success': False, 'error': 'نص الاستفسار فارغ'}
                
            # تنظيف النص
            cleaned_text = self.clean_text(user_text)
            
            # استخراج المعلومات
            cities = self.extract_cities(cleaned_text)
            dates = self.extract_dates(user_text)
            passengers = self.extract_passengers(cleaned_text)
            airlines = self.extract_airlines(user_text)
            
            # التحقق من النجاح
            success = len(cities) >= 2 and len(dates) >= 1
            
            # إنشاء الاستعلام المنظم
            structured_query = None
            if success:
                # استخدام أول تاريخ متوفر
                date_obj = dates[0]
                flight_date = f"{date_obj['year']}-{date_obj['month']:02d}-{date_obj['day']:02d}"
                
                structured_query = {
                    'origin': cities[0]['code'],
                    'destination': cities[1]['code'],
                    'date': flight_date,
                    'adults': passengers['adults']
                }
            
            return {
                'success': success,
                'cities': cities,
                'dates': dates,
                'passengers': passengers,
                'airlines': airlines,
                'query': structured_query,
                'missing_info': self.get_missing_info(cities, dates)
            }
            
        except Exception as e:
            return {'success': False, 'error': f'خطأ في المعالجة: {str(e)}'}

    def get_missing_info(self, cities, dates):
        """الحصول على المعلومات المفقودة"""
        missing = []
        if len(cities) < 2:
            missing.append('المدينة الأصل والوجهة')
        if len(dates) < 1:
            missing.append('تاريخ السفر')
        return missing