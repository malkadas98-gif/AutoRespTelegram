# app/models.py
from datetime import datetime
import json

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'flight_bot.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)




# ✅ جدول تاريخ البحث (بدون علاقة مع users)
class SearchHistory(db.Model):
    __tablename__ = 'search_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False)  # معرف المستخدم كسلسلة نصية
    query_text = db.Column(db.Text, nullable=False)
    origin = db.Column(db.String(10))
    destination = db.Column(db.String(10))
    flight_date = db.Column(db.Date)
    passengers = db.Column(db.Integer, default=1)
    success = db.Column(db.Boolean, default=False)
    flights_found = db.Column(db.Integer, default=0)
    nlp_result = db.Column(db.Text)  # لتخزين نتيجة NLP كـ JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_nlp_result(self, nlp_data):
        """تخزين نتيجة NLP كـ JSON"""
        self.nlp_result = json.dumps(nlp_data, ensure_ascii=False)
    
    def get_nlp_result(self):
        """استرجاع نتيجة NLP من JSON"""
        return json.loads(self.nlp_result) if self.nlp_result else None
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'query_text': self.query_text,
            'origin': self.origin,
            'destination': self.destination,
            'flight_date': self.flight_date.isoformat() if self.flight_date else None,
            'passengers': self.passengers,
            'success': self.success,
            'flights_found': self.flights_found,
            'created_at': self.created_at.isoformat(),
            'nlp_result': self.get_nlp_result()
        }
    
    def __repr__(self):
        return f"<SearchHistory {self.user_id} - {self.origin}-{self.destination}>"


# ✅ جدول إعدادات النظام
class SystemSettings(db.Model):
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(100), nullable=False, unique=True)
    setting_value = db.Column(db.Text)
    description = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'setting_key': self.setting_key,
            'setting_value': self.setting_value,
            'description': self.description,
            'is_active': self.is_active,
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f"<SystemSettings {self.setting_key} = {self.setting_value}>"


# ✅ جدول استخدامات API
class APIUsage(db.Model):
    __tablename__ = 'api_usage'
    
    id = db.Column(db.Integer, primary_key=True)
    endpoint = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.String(100), nullable=True)  # معرف المستخدم كسلسلة نصية
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    response_time = db.Column(db.Float)
    status_code = db.Column(db.Integer)
    ip_address = db.Column(db.String(45))
    
    def to_dict(self):
        return {
            'id': self.id,
            'endpoint': self.endpoint,
            'user_id': self.user_id,
            'timestamp': self.timestamp.isoformat(),
            'response_time': self.response_time,
            'status_code': self.status_code,
            'ip_address': self.ip_address
        }
    
    def __repr__(self):
        return f"<APIUsage {self.endpoint} - {self.status_code} - {self.timestamp}>"

# ✅ جدول الدول الموحد
class Country(db.Model):
    __tablename__ = 'countries'
    
    id = db.Column(db.Integer, primary_key=True)
    arabic_name = db.Column(db.String(100), nullable=False)
    english_name = db.Column(db.String(100), nullable=False)
    country_code = db.Column(db.String(3), nullable=False, unique=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'arabic_name': self.arabic_name,
            'english_name': self.english_name,
            'country_code': self.country_code
        }
    
    def __repr__(self):
        return f"<Country {self.arabic_name} / {self.english_name} ({self.country_code})>"


# ✅ جدول المدن الموحد
class City(db.Model):
    __tablename__ = 'cities'
    
    id = db.Column(db.Integer, primary_key=True)
    arabic_name = db.Column(db.String(100), nullable=False)
    english_name = db.Column(db.String(100), nullable=False)
    iata_code = db.Column(db.String(3), nullable=False, unique=True)
    country_id = db.Column(db.Integer, db.ForeignKey('countries.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    country = db.relationship('Country', backref='cities')
    
    def to_dict(self):
        return {
            'id': self.id,
            'arabic_name': self.arabic_name,
            'english_name': self.english_name,
            'iata_code': self.iata_code,
            'country': self.country.to_dict() if self.country else None
        }
    
    def __repr__(self):
        return f"<City {self.arabic_name} / {self.english_name} ({self.iata_code})>"


# ✅ جدول الأشهر العربية والإنجليزية
class Month(db.Model):
    __tablename__ = 'months'
    
    id = db.Column(db.Integer, primary_key=True)
    arabic_name = db.Column(db.String(20), nullable=False)
    english_name = db.Column(db.String(20), nullable=False)
    month_number = db.Column(db.Integer, nullable=False, unique=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'arabic_name': self.arabic_name,
            'english_name': self.english_name,
            'month_number': self.month_number
        }
    
    def __repr__(self):
        return f"<Month {self.arabic_name} / {self.english_name} ({self.month_number})>"


# ✅ جدول استبدالات النصوص العربية
class ArabicTextReplacement(db.Model):
    __tablename__ = 'arabic_text_replacements'
    
    id = db.Column(db.Integer, primary_key=True)
    original_text = db.Column(db.String(100), nullable=False)
    replacement_text = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'original_text': self.original_text,
            'replacement_text': self.replacement_text,
            'description': self.description
        }
    
    def __repr__(self):
        return f"<ArabicTextReplacement {self.original_text} -> {self.replacement_text}>"


# ✅ جدول شركات الطيران
class Airline(db.Model):
    __tablename__ = 'airlines'
    
    id = db.Column(db.Integer, primary_key=True)
    arabic_name = db.Column(db.String(100), nullable=False)
    english_name = db.Column(db.String(100), nullable=False)
    iata_code = db.Column(db.String(2), nullable=False, unique=True)
    icao_code = db.Column(db.String(3), nullable=False, unique=True)
    country_id = db.Column(db.Integer, db.ForeignKey('countries.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    country = db.relationship('Country', backref='airlines')
    
    def to_dict(self):
        return {
            'id': self.id,
            'arabic_name': self.arabic_name,
            'english_name': self.english_name,
            'iata_code': self.iata_code,
            'icao_code': self.icao_code,
            'country': self.country.to_dict() if self.country else None
        }
    
    def __repr__(self):
        return f"<Airline {self.arabic_name} ({self.iata_code})>"




def init_db(app):
    """تهيئة قاعدة البيانات"""
    db.init_app(app)


def add_initial_data():
    """إضافة البيانات الأولية تلقائياً"""
    try:
        # إضافة الدول العربية الشائعة
        countries_data = [
                {'arabic_name': 'المملكة العربية السعودية', 'english_name': 'Saudi Arabia', 'country_code': 'SAU'},
                {'arabic_name': 'مصر', 'english_name': 'Egypt', 'country_code': 'EGY'},
                {'arabic_name': 'الإمارات العربية المتحدة', 'english_name': 'United Arab Emirates', 'country_code': 'ARE'},
                {'arabic_name': 'الأردن', 'english_name': 'Jordan', 'country_code': 'JOR'},
                {'arabic_name': 'لبنان', 'english_name': 'Lebanon', 'country_code': 'LBN'},
                {'arabic_name': 'الكويت', 'english_name': 'Kuwait', 'country_code': 'KWT'},
                {'arabic_name': 'قطر', 'english_name': 'Qatar', 'country_code': 'QAT'},
                {'arabic_name': 'عُمان', 'english_name': 'Oman', 'country_code': 'OMN'},
                {'arabic_name': 'البحرين', 'english_name': 'Bahrain', 'country_code': 'BHR'},
                {'arabic_name': 'المغرب', 'english_name': 'Morocco', 'country_code': 'MAR'},
                {'arabic_name': 'الجزائر', 'english_name': 'Algeria', 'country_code': 'DZA'},
                {'arabic_name': 'تونس', 'english_name': 'Tunisia', 'country_code': 'TUN'},
                {'arabic_name': 'ليبيا', 'english_name': 'Libya', 'country_code': 'LBY'},
                {'arabic_name': 'السودان', 'english_name': 'Sudan', 'country_code': 'SDN'},
                {'arabic_name': 'اليمن', 'english_name': 'Yemen', 'country_code': 'YEM'},
                {'arabic_name': 'سوريا', 'english_name': 'Syria', 'country_code': 'SYR'},
                {'arabic_name': 'العراق', 'english_name': 'Iraq', 'country_code': 'IRQ'},
                {'arabic_name': 'فلسطين', 'english_name': 'Palestine', 'country_code': 'PSE'},
                {'arabic_name': 'الصومال', 'english_name': 'Somalia', 'country_code': 'SOM'},
                {'arabic_name': 'جيبوتي', 'english_name': 'Djibouti', 'country_code': 'DJI'},
                {'arabic_name': 'جزر القمر', 'english_name': 'Comoros', 'country_code': 'COM'},
                {'arabic_name': 'موريتانيا', 'english_name': 'Mauritania', 'country_code': 'MRT'},
                {'arabic_name': 'الصين', 'english_name': 'China', 'country_code': 'CHN'},
                {'arabic_name': 'اليابان', 'english_name': 'Japan', 'country_code': 'JPN'},
                {'arabic_name': 'الهند', 'english_name': 'India', 'country_code': 'IND'},
                {'arabic_name': 'كوريا الجنوبية', 'english_name': 'South Korea', 'country_code': 'KOR'},
                {'arabic_name': 'سنغافورة', 'english_name': 'Singapore', 'country_code': 'SGP'},
                {'arabic_name': 'تركيا', 'english_name': 'Turkey', 'country_code': 'TUR'},
                {'arabic_name': 'تايلاند', 'english_name': 'Thailand', 'country_code': 'THA'},
                {'arabic_name': 'ماليزيا', 'english_name': 'Malaysia', 'country_code': 'MYS'},
                {'arabic_name': 'إندونيسيا', 'english_name': 'Indonesia', 'country_code': 'IDN'},
                {'arabic_name': 'فيتنام', 'english_name': 'Vietnam', 'country_code': 'VNM'},
                {'arabic_name': 'الفلبين', 'english_name': 'Philippines', 'country_code': 'PHL'},
                {'arabic_name': 'إسرائيل', 'english_name': 'Israel', 'country_code': 'ISR'},
                {'arabic_name': 'باكستان', 'english_name': 'Pakistan', 'country_code': 'PAK'},
                {'arabic_name': 'أذربيجان', 'english_name': 'Azerbaijan', 'country_code': 'AZE'},
                {'arabic_name': 'كازاخستان', 'english_name': 'Kazakhstan', 'country_code': 'KAZ'},
                {'arabic_name': 'أوزبكستان', 'english_name': 'Uzbekistan', 'country_code': 'UZB'},
                {'arabic_name': 'تركمانستان', 'english_name': 'Turkmenistan', 'country_code': 'TKM'},
                {'arabic_name': 'قرغيزستان', 'english_name': 'Kyrgyzstan', 'country_code': 'KGZ'},
                {'arabic_name': 'سريلانكا', 'english_name': 'Sri Lanka', 'country_code': 'LKA'},
                {'arabic_name': 'بنغلاديش', 'english_name': 'Bangladesh', 'country_code': 'BGD'},
                {'arabic_name': 'نيبال', 'english_name': 'Nepal', 'country_code': 'NPL'},
                {'arabic_name': 'تايوان', 'english_name': 'Taiwan', 'country_code': 'TWN'},
                {'arabic_name': 'هونغ كونغ', 'english_name': 'Hong Kong', 'country_code': 'HKG'},
                {'arabic_name': 'ماكاو', 'english_name': 'Macau', 'country_code': 'MAC'},
                {'arabic_name': 'ميانمار', 'english_name': 'Myanmar', 'country_code': 'MMR'},
                {'arabic_name': 'لاوس', 'english_name': 'Laos', 'country_code': 'LAO'},
                {'arabic_name': 'كمبوديا', 'english_name': 'Cambodia', 'country_code': 'KHM'},
                {'arabic_name': 'منغوليا', 'english_name': 'Mongolia', 'country_code': 'MNG'},
                {'arabic_name': 'تيمور الشرقية', 'english_name': 'East Timor', 'country_code': 'TLS'},
                {'arabic_name': 'جورجيا', 'english_name': 'Georgia', 'country_code': 'GEO'},
                {'arabic_name': 'المملكة المتحدة', 'english_name': 'United Kingdom', 'country_code': 'GBR'},
                {'arabic_name': 'فرنسا', 'english_name': 'France', 'country_code': 'FRA'},
                {'arabic_name': 'ألمانيا', 'english_name': 'Germany', 'country_code': 'DEU'},
                {'arabic_name': 'إسبانيا', 'english_name': 'Spain', 'country_code': 'ESP'},
                {'arabic_name': 'إيطاليا', 'english_name': 'Italy', 'country_code': 'ITA'},
                {'arabic_name': 'هولندا', 'english_name': 'Netherlands', 'country_code': 'NLD'},
                {'arabic_name': 'سويسرا', 'english_name': 'Switzerland', 'country_code': 'CHE'},
                {'arabic_name': 'النمسا', 'english_name': 'Austria', 'country_code': 'AUT'},
                {'arabic_name': 'بلجيكا', 'english_name': 'Belgium', 'country_code': 'BEL'},
                {'arabic_name': 'السويد', 'english_name': 'Sweden', 'country_code': 'SWE'},
                {'arabic_name': 'النرويج', 'english_name': 'Norway', 'country_code': 'NOR'},
                {'arabic_name': 'فنلندا', 'english_name': 'Finland', 'country_code': 'FIN'},
                {'arabic_name': 'الدنمارك', 'english_name': 'Denmark', 'country_code': 'DNK'},
                {'arabic_name': 'أيرلندا', 'english_name': 'Ireland', 'country_code': 'IRL'},
                {'arabic_name': 'البرتغال', 'english_name': 'Portugal', 'country_code': 'PRT'},
                {'arabic_name': 'اليونان', 'english_name': 'Greece', 'country_code': 'GRC'},
                {'arabic_name': 'بولندا', 'english_name': 'Poland', 'country_code': 'POL'},
                {'arabic_name': 'التشيك', 'english_name': 'Czech Republic', 'country_code': 'CZE'},
                {'arabic_name': 'المجر', 'english_name': 'Hungary', 'country_code': 'HUN'},
                {'arabic_name': 'رومانيا', 'english_name': 'Romania', 'country_code': 'ROU'},
                {'arabic_name': 'بلغاريا', 'english_name': 'Bulgaria', 'country_code': 'BGR'},
                {'arabic_name': 'كرواتيا', 'english_name': 'Croatia', 'country_code': 'HRV'},
                {'arabic_name': 'صربيا', 'english_name': 'Serbia', 'country_code': 'SRB'},
                {'arabic_name': 'سلوفينيا', 'english_name': 'Slovenia', 'country_code': 'SVN'},
                {'arabic_name': 'سلوفاكيا', 'english_name': 'Slovakia', 'country_code': 'SVK'},
                {'arabic_name': 'أوكرانيا', 'english_name': 'Ukraine', 'country_code': 'UKR'},
                {'arabic_name': 'ليتوانيا', 'english_name': 'Lithuania', 'country_code': 'LTU'},
                {'arabic_name': 'لاتفيا', 'english_name': 'Latvia', 'country_code': 'LVA'},
                {'arabic_name': 'إستونيا', 'english_name': 'Estonia', 'country_code': 'EST'},
                {'arabic_name': 'آيسلندا', 'english_name': 'Iceland', 'country_code': 'ISL'},

                            # 🌍 إفريقيا
                {'arabic_name': 'جنوب أفريقيا', 'english_name': 'South Africa', 'country_code': 'ZAF'},
                {'arabic_name': 'نيجيريا', 'english_name': 'Nigeria', 'country_code': 'NGA'},
                {'arabic_name': 'إثيوبيا', 'english_name': 'Ethiopia', 'country_code': 'ETH'},
                {'arabic_name': 'كينيا', 'english_name': 'Kenya', 'country_code': 'KEN'},
                {'arabic_name': 'المغرب', 'english_name': 'Morocco', 'country_code': 'MAR'},
                {'arabic_name': 'مصر', 'english_name': 'Egypt', 'country_code': 'EGY'},
                {'arabic_name': 'تونس', 'english_name': 'Tunisia', 'country_code': 'TUN'},
                {'arabic_name': 'الجزائر', 'english_name': 'Algeria', 'country_code': 'DZA'},
                {'arabic_name': 'غانا', 'english_name': 'Ghana', 'country_code': 'GHA'},
                {'arabic_name': 'تنزانيا', 'english_name': 'Tanzania', 'country_code': 'TZA'},

                # 🇺🇸 أمريكا الشمالية
                {'arabic_name': 'الولايات المتحدة الأمريكية', 'english_name': 'United States', 'country_code': 'USA'},
                {'arabic_name': 'كندا', 'english_name': 'Canada', 'country_code': 'CAN'},
                {'arabic_name': 'المكسيك', 'english_name': 'Mexico', 'country_code': 'MEX'},
                {'arabic_name': 'جمهورية الدومينيكان', 'english_name': 'Dominican Republic', 'country_code': 'DOM'},
                {'arabic_name': 'كوبا', 'english_name': 'Cuba', 'country_code': 'CUB'},

                # 🇧🇷 أمريكا الجنوبية
                {'arabic_name': 'البرازيل', 'english_name': 'Brazil', 'country_code': 'BRA'},
                {'arabic_name': 'الأرجنتين', 'english_name': 'Argentina', 'country_code': 'ARG'},
                {'arabic_name': 'تشيلي', 'english_name': 'Chile', 'country_code': 'CHL'},
                {'arabic_name': 'كولومبيا', 'english_name': 'Colombia', 'country_code': 'COL'},
                {'arabic_name': 'بيرو', 'english_name': 'Peru', 'country_code': 'PER'},

                # 🇦🇺 أوقيانوسيا / أستراليا
                {'arabic_name': 'أستراليا', 'english_name': 'Australia', 'country_code': 'AUS'},
                {'arabic_name': 'نيوزيلندا', 'english_name': 'New Zealand', 'country_code': 'NZL'},
                {'arabic_name': 'فيجي', 'english_name': 'Fiji', 'country_code': 'FJI'},
                {'arabic_name': 'بابوا غينيا الجديدة', 'english_name': 'Papua New Guinea', 'country_code': 'PNG'}
                         
         ]
        
        for country_data in countries_data:
            if not Country.query.filter_by(country_code=country_data['country_code']).first():
                country = Country(**country_data)
                db.session.add(country)
                print(f"تم إضافة دولة: {country_data['arabic_name']}")
        
        # إضافة الأشهر العربية والإنجليزية
        months_data = [
            {'arabic_name': 'يناير', 'english_name': 'January', 'month_number': 1},
            {'arabic_name': 'فبراير', 'english_name': 'February', 'month_number': 2},
            {'arabic_name': 'مارس', 'english_name': 'March', 'month_number': 3},
            {'arabic_name': 'أبريل', 'english_name': 'April', 'month_number': 4},
            {'arabic_name': 'مايو', 'english_name': 'May', 'month_number': 5},
            {'arabic_name': 'يونيو', 'english_name': 'June', 'month_number': 6},
            {'arabic_name': 'يوليو', 'english_name': 'July', 'month_number': 7},
            {'arabic_name': 'أغسطس', 'english_name': 'August', 'month_number': 8},
            {'arabic_name': 'سبتمبر', 'english_name': 'September', 'month_number': 9},
            {'arabic_name': 'أكتوبر', 'english_name': 'October', 'month_number': 10},
            {'arabic_name': 'نوفمبر', 'english_name': 'November', 'month_number': 11},
            {'arabic_name': 'ديسمبر', 'english_name': 'December', 'month_number': 12},
        ]
        
        for month_data in months_data:
            if not Month.query.filter_by(month_number=month_data['month_number']).first():
                month = Month(**month_data)
                db.session.add(month)
                print(f"تم إضافة شهر: {month_data['arabic_name']}")
        
        # إضافة بعض المدن الرئيسية
        cities_data = [
               # 🇸🇦 السعودية
            {'arabic_name': 'الرياض', 'english_name': 'Riyadh', 'country_code': 'SAU', 'iata_code': 'RUH'},
            {'arabic_name': 'جدة', 'english_name': 'Jeddah', 'country_code': 'SAU', 'iata_code': 'JED'},
            {'arabic_name': 'الدمام', 'english_name': 'Dammam', 'country_code': 'SAU', 'iata_code': 'DMM'},
            {'arabic_name': 'المدينة المنورة', 'english_name': 'Medina', 'country_code': 'SAU', 'iata_code': 'MED'},

            # 🇪🇬 مصر
            {'arabic_name': 'القاهرة', 'english_name': 'Cairo', 'country_code': 'EGY', 'iata_code': 'CAI'},
            {'arabic_name': 'الإسكندرية', 'english_name': 'Alexandria', 'country_code': 'EGY', 'iata_code': 'HBE'},
            {'arabic_name': 'شرم الشيخ', 'english_name': 'Sharm El Sheikh', 'country_code': 'EGY', 'iata_code': 'SSH'},
            {'arabic_name': 'الغردقة', 'english_name': 'Hurghada', 'country_code': 'EGY', 'iata_code': 'HRG'},

            # 🇦🇪 الإمارات
            {'arabic_name': 'دبي', 'english_name': 'Dubai', 'country_code': 'ARE', 'iata_code': 'DXB'},
            {'arabic_name': 'أبوظبي', 'english_name': 'Abu Dhabi', 'country_code': 'ARE', 'iata_code': 'AUH'},
            {'arabic_name': 'الشارقة', 'english_name': 'Sharjah', 'country_code': 'ARE', 'iata_code': 'SHJ'},

            # 🇶🇦 قطر
            {'arabic_name': 'الدوحة', 'english_name': 'Doha', 'country_code': 'QAT', 'iata_code': 'DOH'},

            # 🇴🇲 عمان
            {'arabic_name': 'مسقط', 'english_name': 'Muscat', 'country_code': 'OMN', 'iata_code': 'MCT'},
            {'arabic_name': 'صلالة', 'english_name': 'Salalah', 'country_code': 'OMN', 'iata_code': 'SLL'},

            # 🇧🇭 البحرين
            {'arabic_name': 'المنامة', 'english_name': 'Manama', 'country_code': 'BHR', 'iata_code': 'BAH'},

            # 🇰🇼 الكويت
            {'arabic_name': 'الكويت', 'english_name': 'Kuwait City', 'country_code': 'KWT', 'iata_code': 'KWI'},

            # 🇯🇴 الأردن
            {'arabic_name': 'عمّان', 'english_name': 'Amman', 'country_code': 'JOR', 'iata_code': 'AMM'},
            {'arabic_name': 'العقبة', 'english_name': 'Aqaba', 'country_code': 'JOR', 'iata_code': 'AQJ'},

            # 🇱🇧 لبنان
            {'arabic_name': 'بيروت', 'english_name': 'Beirut', 'country_code': 'LBN', 'iata_code': 'BEY'},

            # 🇮🇶 العراق
            {'arabic_name': 'بغداد', 'english_name': 'Baghdad', 'country_code': 'IRQ', 'iata_code': 'BGW'},
            {'arabic_name': 'أربيل', 'english_name': 'Erbil', 'country_code': 'IRQ', 'iata_code': 'EBL'},
            {'arabic_name': 'البصرة', 'english_name': 'Basra', 'country_code': 'IRQ', 'iata_code': 'BSR'},

            # 🇸🇾 سوريا
            {'arabic_name': 'دمشق', 'english_name': 'Damascus', 'country_code': 'SYR', 'iata_code': 'DAM'},
            {'arabic_name': 'حلب', 'english_name': 'Aleppo', 'country_code': 'SYR', 'iata_code': 'ALP'},

            # 🇱🇾 ليبيا
            {'arabic_name': 'طرابلس', 'english_name': 'Tripoli', 'country_code': 'LBY', 'iata_code': 'TIP'},
            {'arabic_name': 'بنغازي', 'english_name': 'Benghazi', 'country_code': 'LBY', 'iata_code': 'BEN'},

            # 🇸🇩 السودان
            {'arabic_name': 'الخرطوم', 'english_name': 'Khartoum', 'country_code': 'SDN', 'iata_code': 'KRT'},

            # 🇾🇪 اليمن
            {'arabic_name': 'صنعاء', 'english_name': 'Sana’a', 'country_code': 'YEM', 'iata_code': 'SAH'},
            {'arabic_name': 'عدن', 'english_name': 'Aden', 'country_code': 'YEM', 'iata_code': 'ADE'},

            # 🇵🇸 فلسطين
            {'arabic_name': 'القدس', 'english_name': 'Jerusalem', 'country_code': 'PSE', 'iata_code': '---'},
            {'arabic_name': 'رام الله', 'english_name': 'Ramallah', 'country_code': 'PSE', 'iata_code': '---'},

            # 🇲🇦 المغرب
            {'arabic_name': 'الدار البيضاء', 'english_name': 'Casablanca', 'country_code': 'MAR', 'iata_code': 'CMN'},
            {'arabic_name': 'مراكش', 'english_name': 'Marrakesh', 'country_code': 'MAR', 'iata_code': 'RAK'},
            {'arabic_name': 'الرباط', 'english_name': 'Rabat', 'country_code': 'MAR', 'iata_code': 'RBA'},

            # 🇩🇿 الجزائر
            {'arabic_name': 'الجزائر', 'english_name': 'Algiers', 'country_code': 'DZA', 'iata_code': 'ALG'},
            {'arabic_name': 'وهران', 'english_name': 'Oran', 'country_code': 'DZA', 'iata_code': 'ORN'},

            # 🇹🇳 تونس
            {'arabic_name': 'تونس', 'english_name': 'Tunis', 'country_code': 'TUN', 'iata_code': 'TUN'},
            {'arabic_name': 'سوسة', 'english_name': 'Sousse', 'country_code': 'TUN', 'iata_code': '---'},

            # 🇲🇷 موريتانيا
            {'arabic_name': 'نواكشوط', 'english_name': 'Nouakchott', 'country_code': 'MRT', 'iata_code': 'NKC'},

            # 🇸🇴 الصومال
            {'arabic_name': 'مقديشو', 'english_name': 'Mogadishu', 'country_code': 'SOM', 'iata_code': 'MGQ'},

            # 🇩🇯 جيبوتي
            {'arabic_name': 'جيبوتي', 'english_name': 'Djibouti', 'country_code': 'DJI', 'iata_code': 'JIB'},

            # 🇰🇲 جزر القمر
            {'arabic_name': 'موروني', 'english_name': 'Moroni', 'country_code': 'COM', 'iata_code': 'HAH'},

            
    # 🇨🇳 الصين
    {'arabic_name': 'بكين', 'english_name': 'Beijing', 'country_code': 'CHN', 'iata_code': 'PEK'},
    {'arabic_name': 'شانغهاي', 'english_name': 'Shanghai', 'country_code': 'CHN', 'iata_code': 'PVG'},
    {'arabic_name': 'غوانزو', 'english_name': 'Guangzhou', 'country_code': 'CHN', 'iata_code': 'CAN'},
    {'arabic_name': 'شينزين', 'english_name': 'Shenzhen', 'country_code': 'CHN', 'iata_code': 'SZX'},

    # 🇯🇵 اليابان
    {'arabic_name': 'طوكيو', 'english_name': 'Tokyo', 'country_code': 'JPN', 'iata_code': 'HND'},
    {'arabic_name': 'أوساكا', 'english_name': 'Osaka', 'country_code': 'JPN', 'iata_code': 'KIX'},
    {'arabic_name': 'ناغويا', 'english_name': 'Nagoya', 'country_code': 'JPN', 'iata_code': 'NGO'},

    # 🇮🇳 الهند
    {'arabic_name': 'نيودلهي', 'english_name': 'New Delhi', 'country_code': 'IND', 'iata_code': 'DEL'},
    {'arabic_name': 'مومباي', 'english_name': 'Mumbai', 'country_code': 'IND', 'iata_code': 'BOM'},
    {'arabic_name': 'بنغالور', 'english_name': 'Bangalore', 'country_code': 'IND', 'iata_code': 'BLR'},
    {'arabic_name': 'حيدر آباد', 'english_name': 'Hyderabad', 'country_code': 'IND', 'iata_code': 'HYD'},
    {'arabic_name': 'تشيناي', 'english_name': 'Chennai', 'country_code': 'IND', 'iata_code': 'MAA'},

    # 🇸🇬 سنغافورة
    {'arabic_name': 'سنغافورة', 'english_name': 'Singapore', 'country_code': 'SGP', 'iata_code': 'SIN'},

    # 🇹🇭 تايلاند
    {'arabic_name': 'بانكوك', 'english_name': 'Bangkok', 'country_code': 'THA', 'iata_code': 'BKK'},
    {'arabic_name': 'فوكيت', 'english_name': 'Phuket', 'country_code': 'THA', 'iata_code': 'HKT'},

    # 🇲🇾 ماليزيا
    {'arabic_name': 'كوالالمبور', 'english_name': 'Kuala Lumpur', 'country_code': 'MYS', 'iata_code': 'KUL'},
    {'arabic_name': 'بينانغ', 'english_name': 'Penang', 'country_code': 'MYS', 'iata_code': 'PEN'},

    # 🇮🇩 إندونيسيا
    {'arabic_name': 'جاكرتا', 'english_name': 'Jakarta', 'country_code': 'IDN', 'iata_code': 'CGK'},
    {'arabic_name': 'بالي', 'english_name': 'Bali (Denpasar)', 'country_code': 'IDN', 'iata_code': 'DPS'},

    # 🇻🇳 فيتنام
    {'arabic_name': 'هانوي', 'english_name': 'Hanoi', 'country_code': 'VNM', 'iata_code': 'HAN'},
    {'arabic_name': 'مدينة هو تشي منه', 'english_name': 'Ho Chi Minh City', 'country_code': 'VNM', 'iata_code': 'SGN'},

    # 🇵🇭 الفلبين
    {'arabic_name': 'مانيلا', 'english_name': 'Manila', 'country_code': 'PHL', 'iata_code': 'MNL'},
    {'arabic_name': 'سيبو', 'english_name': 'Cebu', 'country_code': 'PHL', 'iata_code': 'CEB'},

    # 🇰🇷 كوريا الجنوبية
    {'arabic_name': 'سيول', 'english_name': 'Seoul', 'country_code': 'KOR', 'iata_code': 'ICN'},
    {'arabic_name': 'بوسان', 'english_name': 'Busan', 'country_code': 'KOR', 'iata_code': 'PUS'},

    # 🇹🇷 تركيا (جزء آسيوي وأوروبي لكنها محور رئيسي)
    {'arabic_name': 'إسطنبول', 'english_name': 'Istanbul', 'country_code': 'TUR', 'iata_code': 'IST'},
    {'arabic_name': 'أنقرة', 'english_name': 'Ankara', 'country_code': 'TUR', 'iata_code': 'ESB'},

    # 🇮🇱 إسرائيل
    {'arabic_name': 'تل أبيب', 'english_name': 'Tel Aviv', 'country_code': 'ISR', 'iata_code': 'TLV'},

    # 🇵🇰 باكستان
    {'arabic_name': 'كراتشي', 'english_name': 'Karachi', 'country_code': 'PAK', 'iata_code': 'KHI'},
    {'arabic_name': 'إسلام آباد', 'english_name': 'Islamabad', 'country_code': 'PAK', 'iata_code': 'ISB'},
    {'arabic_name': 'لاهور', 'english_name': 'Lahore', 'country_code': 'PAK', 'iata_code': 'LHE'},

    # 🇱🇰 سريلانكا
    {'arabic_name': 'كولومبو', 'english_name': 'Colombo', 'country_code': 'LKA', 'iata_code': 'CMB'},

    # 🇧🇩 بنغلاديش
    {'arabic_name': 'دكا', 'english_name': 'Dhaka', 'country_code': 'BGD', 'iata_code': 'DAC'},

    # 🇳🇵 نيبال
    {'arabic_name': 'كاتماندو', 'english_name': 'Kathmandu', 'country_code': 'NPL', 'iata_code': 'KTM'},

    # 🇹🇼 تايوان
    {'arabic_name': 'تايبيه', 'english_name': 'Taipei', 'country_code': 'TWN', 'iata_code': 'TPE'},

    # 🇭🇰 هونغ كونغ
    {'arabic_name': 'هونغ كونغ', 'english_name': 'Hong Kong', 'country_code': 'HKG', 'iata_code': 'HKG'},

    # 🇰🇿 كازاخستان
    {'arabic_name': 'ألماتي', 'english_name': 'Almaty', 'country_code': 'KAZ', 'iata_code': 'ALA'},
    {'arabic_name': 'أستانا', 'english_name': 'Astana', 'country_code': 'KAZ', 'iata_code': 'NQZ'},

    # 🇦🇿 أذربيجان
    {'arabic_name': 'باكو', 'english_name': 'Baku', 'country_code': 'AZE', 'iata_code': 'GYD'},

    # 🇺🇿 أوزبكستان
    {'arabic_name': 'طشقند', 'english_name': 'Tashkent', 'country_code': 'UZB', 'iata_code': 'TAS'},

    # 🇬🇪 جورجيا
    {'arabic_name': 'تبليسي', 'english_name': 'Tbilisi', 'country_code': 'GEO', 'iata_code': 'TBS'},

    # 🇬🇧 المملكة المتحدة
    {'arabic_name': 'لندن', 'english_name': 'London', 'country_code': 'GBR', 'iata_code': 'LHR'},
    {'arabic_name': 'مانشستر', 'english_name': 'Manchester', 'country_code': 'GBR', 'iata_code': 'MAN'},
    {'arabic_name': 'برمنغهام', 'english_name': 'Birmingham', 'country_code': 'GBR', 'iata_code': 'BHX'},
    {'arabic_name': 'إدنبرة', 'english_name': 'Edinburgh', 'country_code': 'GBR', 'iata_code': 'EDI'},

    # 🇫🇷 فرنسا
    {'arabic_name': 'باريس', 'english_name': 'Paris', 'country_code': 'FRA', 'iata_code': 'CDG'},
    {'arabic_name': 'نيس', 'english_name': 'Nice', 'country_code': 'FRA', 'iata_code': 'NCE'},
    {'arabic_name': 'ليون', 'english_name': 'Lyon', 'country_code': 'FRA', 'iata_code': 'LYS'},

    # 🇩🇪 ألمانيا
    {'arabic_name': 'فرانكفورت', 'english_name': 'Frankfurt', 'country_code': 'DEU', 'iata_code': 'FRA'},
    {'arabic_name': 'ميونخ', 'english_name': 'Munich', 'country_code': 'DEU', 'iata_code': 'MUC'},
    {'arabic_name': 'برلين', 'english_name': 'Berlin', 'country_code': 'DEU', 'iata_code': 'BER'},
    {'arabic_name': 'دوسلدورف', 'english_name': 'Düsseldorf', 'country_code': 'DEU', 'iata_code': 'DUS'},

    # 🇪🇸 إسبانيا
    {'arabic_name': 'مدريد', 'english_name': 'Madrid', 'country_code': 'ESP', 'iata_code': 'MAD'},
    {'arabic_name': 'برشلونة', 'english_name': 'Barcelona', 'country_code': 'ESP', 'iata_code': 'BCN'},
    {'arabic_name': 'مالقا', 'english_name': 'Malaga', 'country_code': 'ESP', 'iata_code': 'AGP'},
    {'arabic_name': 'إشبيلية', 'english_name': 'Seville', 'country_code': 'ESP', 'iata_code': 'SVQ'},

    # 🇮🇹 إيطاليا
    {'arabic_name': 'روما', 'english_name': 'Rome', 'country_code': 'ITA', 'iata_code': 'FCO'},
    {'arabic_name': 'ميلانو', 'english_name': 'Milan', 'country_code': 'ITA', 'iata_code': 'MXP'},
    {'arabic_name': 'فينيسيا', 'english_name': 'Venice', 'country_code': 'ITA', 'iata_code': 'VCE'},
    {'arabic_name': 'نابولي', 'english_name': 'Naples', 'country_code': 'ITA', 'iata_code': 'NAP'},

    # 🇳🇱 هولندا
    {'arabic_name': 'أمستردام', 'english_name': 'Amsterdam', 'country_code': 'NLD', 'iata_code': 'AMS'},

    # 🇨🇭 سويسرا
    {'arabic_name': 'زيورخ', 'english_name': 'Zurich', 'country_code': 'CHE', 'iata_code': 'ZRH'},
    {'arabic_name': 'جنيف', 'english_name': 'Geneva', 'country_code': 'CHE', 'iata_code': 'GVA'},

    # 🇦🇹 النمسا
    {'arabic_name': 'فيينا', 'english_name': 'Vienna', 'country_code': 'AUT', 'iata_code': 'VIE'},

    # 🇸🇪 السويد
    {'arabic_name': 'ستوكهولم', 'english_name': 'Stockholm', 'country_code': 'SWE', 'iata_code': 'ARN'},

    # 🇳🇴 النرويج
    {'arabic_name': 'أوسلو', 'english_name': 'Oslo', 'country_code': 'NOR', 'iata_code': 'OSL'},

    # 🇩🇰 الدنمارك
    {'arabic_name': 'كوبنهاغن', 'english_name': 'Copenhagen', 'country_code': 'DNK', 'iata_code': 'CPH'},

    # 🇫🇮 فنلندا
    {'arabic_name': 'هلسنكي', 'english_name': 'Helsinki', 'country_code': 'FIN', 'iata_code': 'HEL'},

    # 🇷🇺 روسيا
    {'arabic_name': 'موسكو', 'english_name': 'Moscow', 'country_code': 'RUS', 'iata_code': 'SVO'},
    {'arabic_name': 'سانت بطرسبرغ', 'english_name': 'Saint Petersburg', 'country_code': 'RUS', 'iata_code': 'LED'},

    # 🇵🇱 بولندا
    {'arabic_name': 'وارسو', 'english_name': 'Warsaw', 'country_code': 'POL', 'iata_code': 'WAW'},

    # 🇨🇿 التشيك
    {'arabic_name': 'براغ', 'english_name': 'Prague', 'country_code': 'CZE', 'iata_code': 'PRG'},

    # 🇭🇺 المجر
    {'arabic_name': 'بودابست', 'english_name': 'Budapest', 'country_code': 'HUN', 'iata_code': 'BUD'},

    # 🇬🇷 اليونان
    {'arabic_name': 'أثينا', 'english_name': 'Athens', 'country_code': 'GRC', 'iata_code': 'ATH'},
    {'arabic_name': 'سانتوريني', 'english_name': 'Santorini', 'country_code': 'GRC', 'iata_code': 'JTR'},

    # 🇵🇹 البرتغال
    {'arabic_name': 'لشبونة', 'english_name': 'Lisbon', 'country_code': 'PRT', 'iata_code': 'LIS'},
    {'arabic_name': 'بورتو', 'english_name': 'Porto', 'country_code': 'PRT', 'iata_code': 'OPO'},

    # 🇧🇪 بلجيكا
    {'arabic_name': 'بروكسل', 'english_name': 'Brussels', 'country_code': 'BEL', 'iata_code': 'BRU'},

    # 🇮🇪 إيرلندا
    {'arabic_name': 'دبلن', 'english_name': 'Dublin', 'country_code': 'IRL', 'iata_code': 'DUB'},

    # 🇮🇸 آيسلندا
    {'arabic_name': 'ريكيافيك', 'english_name': 'Reykjavik', 'country_code': 'ISL', 'iata_code': 'KEF'},

    # 🇺🇦 أوكرانيا
    {'arabic_name': 'كييف', 'english_name': 'Kyiv', 'country_code': 'UKR', 'iata_code': 'KBP'},

    # 🇷🇴 رومانيا
    {'arabic_name': 'بوخارست', 'english_name': 'Bucharest', 'country_code': 'ROU', 'iata_code': 'OTP'},

    # 🇷🇸 صربيا
    {'arabic_name': 'بلغراد', 'english_name': 'Belgrade', 'country_code': 'SRB', 'iata_code': 'BEG'},

    # 🇭🇷 كرواتيا
    {'arabic_name': 'زغرب', 'english_name': 'Zagreb', 'country_code': 'HRV', 'iata_code': 'ZAG'},

    # 🇨🇭 مالطا
    {'arabic_name': 'فاليتا', 'english_name': 'Valletta', 'country_code': 'MLT', 'iata_code': 'MLA'},
    
    # 🌍 إفريقيا
    # 🇪🇬 مصر (ذكرت سابقاً، لكن أهم مطاراتها الدولية مذكورة فقط للتكامل)
    {'arabic_name': 'القاهرة', 'english_name': 'Cairo', 'country_code': 'EGY', 'iata_code': 'CAI'},

    # 🇿🇦 جنوب أفريقيا
    {'arabic_name': 'جوهانسبرغ', 'english_name': 'Johannesburg', 'country_code': 'ZAF', 'iata_code': 'JNB'},
    {'arabic_name': 'كيب تاون', 'english_name': 'Cape Town', 'country_code': 'ZAF', 'iata_code': 'CPT'},
    {'arabic_name': 'ديربان', 'english_name': 'Durban', 'country_code': 'ZAF', 'iata_code': 'DUR'},

    # 🇪🇹 إثيوبيا
    {'arabic_name': 'أديس أبابا', 'english_name': 'Addis Ababa', 'country_code': 'ETH', 'iata_code': 'ADD'},

    # 🇰🇪 كينيا
    {'arabic_name': 'نيروبي', 'english_name': 'Nairobi', 'country_code': 'KEN', 'iata_code': 'NBO'},

    # 🇳🇬 نيجيريا
    {'arabic_name': 'لاغوس', 'english_name': 'Lagos', 'country_code': 'NGA', 'iata_code': 'LOS'},
    {'arabic_name': 'أبوجا', 'english_name': 'Abuja', 'country_code': 'NGA', 'iata_code': 'ABV'},

    # 🇲🇦 المغرب
    {'arabic_name': 'الدار البيضاء', 'english_name': 'Casablanca', 'country_code': 'MAR', 'iata_code': 'CMN'},

    # 🇹🇳 تونس
    {'arabic_name': 'تونس', 'english_name': 'Tunis', 'country_code': 'TUN', 'iata_code': 'TUN'},

    # 🇩🇿 الجزائر
    {'arabic_name': 'الجزائر', 'english_name': 'Algiers', 'country_code': 'DZA', 'iata_code': 'ALG'},

    # 🇸🇳 السنغال
    {'arabic_name': 'داكار', 'english_name': 'Dakar', 'country_code': 'SEN', 'iata_code': 'DSS'},

    # 🇪🇬 مصر
    {'arabic_name': 'الغردقة', 'english_name': 'Hurghada', 'country_code': 'EGY', 'iata_code': 'HRG'},

    # 🇪🇹 تنزانيا
    {'arabic_name': 'دار السلام', 'english_name': 'Dar es Salaam', 'country_code': 'TZA', 'iata_code': 'DAR'},

    # 🇺🇬 أوغندا
    {'arabic_name': 'عنتيبي', 'english_name': 'Entebbe', 'country_code': 'UGA', 'iata_code': 'EBB'},

    # 🇷🇼 رواندا
    {'arabic_name': 'كيغالي', 'english_name': 'Kigali', 'country_code': 'RWA', 'iata_code': 'KGL'},

    # 🇪🇷 إريتريا
    {'arabic_name': 'أسمرة', 'english_name': 'Asmara', 'country_code': 'ERI', 'iata_code': 'ASM'},

    # 🌎 أمريكا الشمالية
    # 🇺🇸 الولايات المتحدة
    {'arabic_name': 'نيويورك', 'english_name': 'New York', 'country_code': 'USA', 'iata_code': 'JFK'},
    {'arabic_name': 'لوس أنجلوس', 'english_name': 'Los Angeles', 'country_code': 'USA', 'iata_code': 'LAX'},
    {'arabic_name': 'شيكاغو', 'english_name': 'Chicago', 'country_code': 'USA', 'iata_code': 'ORD'},
    {'arabic_name': 'ميامي', 'english_name': 'Miami', 'country_code': 'USA', 'iata_code': 'MIA'},
    {'arabic_name': 'دالاس', 'english_name': 'Dallas', 'country_code': 'USA', 'iata_code': 'DFW'},
    {'arabic_name': 'سان فرانسيسكو', 'english_name': 'San Francisco', 'country_code': 'USA', 'iata_code': 'SFO'},
    {'arabic_name': 'هيوستن', 'english_name': 'Houston', 'country_code': 'USA', 'iata_code': 'IAH'},
    {'arabic_name': 'أتلانتا', 'english_name': 'Atlanta', 'country_code': 'USA', 'iata_code': 'ATL'},
    {'arabic_name': 'بوسطن', 'english_name': 'Boston', 'country_code': 'USA', 'iata_code': 'BOS'},
    {'arabic_name': 'واشنطن', 'english_name': 'Washington D.C.', 'country_code': 'USA', 'iata_code': 'IAD'},

    # 🇨🇦 كندا
    {'arabic_name': 'تورونتو', 'english_name': 'Toronto', 'country_code': 'CAN', 'iata_code': 'YYZ'},
    {'arabic_name': 'فانكوفر', 'english_name': 'Vancouver', 'country_code': 'CAN', 'iata_code': 'YVR'},
    {'arabic_name': 'مونتريال', 'english_name': 'Montreal', 'country_code': 'CAN', 'iata_code': 'YUL'},
    {'arabic_name': 'كالجاري', 'english_name': 'Calgary', 'country_code': 'CAN', 'iata_code': 'YYC'},

    # 🇲🇽 المكسيك
    {'arabic_name': 'مكسيكو سيتي', 'english_name': 'Mexico City', 'country_code': 'MEX', 'iata_code': 'MEX'},
    {'arabic_name': 'كانكون', 'english_name': 'Cancun', 'country_code': 'MEX', 'iata_code': 'CUN'},
    {'arabic_name': 'غوادالاخارا', 'english_name': 'Guadalajara', 'country_code': 'MEX', 'iata_code': 'GDL'},

    # 🌎 أمريكا الجنوبية
    # 🇧🇷 البرازيل
    {'arabic_name': 'ريو دي جانيرو', 'english_name': 'Rio de Janeiro', 'country_code': 'BRA', 'iata_code': 'GIG'},
    {'arabic_name': 'ساو باولو', 'english_name': 'São Paulo', 'country_code': 'BRA', 'iata_code': 'GRU'},

    # 🇦🇷 الأرجنتين
    {'arabic_name': 'بوينس آيرس', 'english_name': 'Buenos Aires', 'country_code': 'ARG', 'iata_code': 'EZE'},

    # 🇨🇱 تشيلي
    {'arabic_name': 'سانتياغو', 'english_name': 'Santiago', 'country_code': 'CHL', 'iata_code': 'SCL'},

    # 🇨🇴 كولومبيا
    {'arabic_name': 'بوغوتا', 'english_name': 'Bogotá', 'country_code': 'COL', 'iata_code': 'BOG'},

    # 🇵🇪 بيرو
    {'arabic_name': 'ليما', 'english_name': 'Lima', 'country_code': 'PER', 'iata_code': 'LIM'},

    # 🇪🇨 الإكوادور
    {'arabic_name': 'كيتو', 'english_name': 'Quito', 'country_code': 'ECU', 'iata_code': 'UIO'},

    # 🇺🇾 أوروغواي
    {'arabic_name': 'مونتيفيديو', 'english_name': 'Montevideo', 'country_code': 'URY', 'iata_code': 'MVD'},

    # 🌏 أستراليا وأوقيانوسيا
    # 🇦🇺 أستراليا
    {'arabic_name': 'سيدني', 'english_name': 'Sydney', 'country_code': 'AUS', 'iata_code': 'SYD'},
    {'arabic_name': 'ملبورن', 'english_name': 'Melbourne', 'country_code': 'AUS', 'iata_code': 'MEL'},
    {'arabic_name': 'بريزبن', 'english_name': 'Brisbane', 'country_code': 'AUS', 'iata_code': 'BNE'},
    {'arabic_name': 'بيرث', 'english_name': 'Perth', 'country_code': 'AUS', 'iata_code': 'PER'},

    # 🇳🇿 نيوزيلندا
    {'arabic_name': 'أوكلاند', 'english_name': 'Auckland', 'country_code': 'NZL', 'iata_code': 'AKL'},
    {'arabic_name': 'ويلينغتون', 'english_name': 'Wellington', 'country_code': 'NZL', 'iata_code': 'WLG'},

  
# الإمارات
{'arabic_name':'دبي – مطار آل مكتوم','english_name':'Dubai Al Maktoum','country_code':'ARE','iata_code':'DWC','city_arabic':'دبي','city_english':'Dubai'},

# تركيا
{'arabic_name':'إسطنبول – صبيحة جوكتشن','english_name':'Istanbul Sabiha Gokcen','country_code':'TUR','iata_code':'SAW','city_arabic':'إسطنبول','city_english':'Istanbul'},
{'arabic_name':'أنقرة – إيسينبوغا (مطار قديم)','english_name':'Ankara Esenboga (secondary)','country_code':'TUR','iata_code':'ESB','city_arabic':'أنقرة','city_english':'Ankara'},

# المملكة المتحدة (لندن وغيرها)
{'arabic_name':'لندن – غاتويك','english_name':'London Gatwick','country_code':'GBR','iata_code':'LGW','city_arabic':'لندن','city_english':'London'},
{'arabic_name':'لندن – ستانستد','english_name':'London Stansted','country_code':'GBR','iata_code':'STN','city_arabic':'لندن','city_english':'London'},
{'arabic_name':'لندن – لوتون','english_name':'London Luton','country_code':'GBR','iata_code':'LTN','city_arabic':'لندن','city_english':'London'},
{'arabic_name':'لندن – سيتي','english_name':'London City','country_code':'GBR','iata_code':'LCY','city_arabic':'لندن','city_english':'London'},
{'arabic_name':'لندن – ساوثيند','english_name':'London Southend','country_code':'GBR','iata_code':'SEN','city_arabic':'لندن','city_english':'London'},

# الولايات المتحدة (نيويورك، واشنطن، لوس أنجلوس، شيكاغو،...) — الثانوية فقط
{'arabic_name':'نيويورك – نيوارك','english_name':'Newark Liberty','country_code':'USA','iata_code':'EWR','city_arabic':'نيويورك','city_english':'New York'},
{'arabic_name':'نيويورك – لا غارديا','english_name':'LaGuardia','country_code':'USA','iata_code':'LGA','city_arabic':'نيويورك','city_english':'New York'},
{'arabic_name':'نيويورك – وستشستر/هايتسبرن','english_name':'Westchester (HPN)','country_code':'USA','iata_code':'HPN','city_arabic':'نيويورك','city_english':'New York'},
{'arabic_name':'نيويورك – لونغ آيلاند ماك آرثر','english_name':'Long Island MacArthur (ISP)','country_code':'USA','iata_code':'ISP','city_arabic':'نيويورك','city_english':'New York'},

{'arabic_name':'واشنطن – دولس','english_name':'Washington Dulles','country_code':'USA','iata_code':'IAD','city_arabic':'واشنطن','city_english':'Washington D.C.'},
{'arabic_name':'واشنطن – بالتيمور واشنطن','english_name':'Baltimore/Washington (BWI)','country_code':'USA','iata_code':'BWI','city_arabic':'واشنطن','city_english':'Washington D.C.'},

{'arabic_name':'لوس أنجلوس – جون وين/أورانج كاونتي','english_name':'John Wayne/Orange County (SNA)','country_code':'USA','iata_code':'SNA','city_arabic':'لوس أنجلوس','city_english':'Los Angeles'},
{'arabic_name':'لوس أنجلوس – بيربانك','english_name':'Hollywood Burbank (BUR)','country_code':'USA','iata_code':'BUR','city_arabic':'لوس أنجلوس','city_english':'Los Angeles'},
{'arabic_name':'لوس أنجلوس – لونغ بيتش','english_name':'Long Beach (LGB)','country_code':'USA','iata_code':'LGB','city_arabic':'لوس أنجلوس','city_english':'Los Angeles'},
{'arabic_name':'لوس أنجلوس – أونتاريو','english_name':'Ontario (ONT)','country_code':'USA','iata_code':'ONT','city_arabic':'لوس أنجلوس','city_english':'Los Angeles'},

{'arabic_name':'شيكاغو – ميدواي','english_name':'Chicago Midway (MDW)','country_code':'USA','iata_code':'MDW','city_arabic':'شيكاغو','city_english':'Chicago'},

# كندا
{'arabic_name':'تورونتو – بيلي بيشوب (جزيرة)','english_name':'Billy Bishop Toronto Island (YTZ)','country_code':'CAN','iata_code':'YTZ','city_arabic':'تورونتو','city_english':'Toronto'},
{'arabic_name':'مونتريال – سانت هوبيرت / ماس','english_name':'Montreal Saint-Hubert (YHU)','country_code':'CAN','iata_code':'YHU','city_arabic':'مونتريال','city_english':'Montréal'},

# المكسيك (مطار كانكون ثانوي لوجهات أخرى لا يعتبر ثانوي داخل مدينة واحدة كثيراً)
# (لايوجد ثانوي قوي لمدينة مكسيكو سيتي في نفس المستوى هنا) 

# البرازيل
{'arabic_name':'ساو باولو – كونغونهاس','english_name':'São Paulo Congonhas (CGH)','country_code':'BRA','iata_code':'CGH','city_arabic':'ساو باولو','city_english':'São Paulo'},
{'arabic_name':'ريو دي جانيرو – سانتوس دومونت','english_name':'Santos Dumont (SDU)','country_code':'BRA','iata_code':'SDU','city_arabic':'ريو دي جانيرو','city_english':'Rio de Janeiro'},

# الأرجنتين
{'arabic_name':'بوينس آيرس – أيروبارك خورخي نيوبرى','english_name':'Aeroparque Jorge Newbery (AEP)','country_code':'ARG','iata_code':'AEP','city_arabic':'بوينس آيرس','city_english':'Buenos Aires'},

# فرنسا (الثانوي لباريس)
{'arabic_name':'باريس – أورلي','english_name':'Paris Orly (ORY)','country_code':'FRA','iata_code':'ORY','city_arabic':'باريس','city_english':'Paris'},
{'arabic_name':'باريس – بوفيه','english_name':'Beauvais-Tillé (BVA)','country_code':'FRA','iata_code':'BVA','city_arabic':'باريس','city_english':'Paris'},

# ألمانيا (برلين ثانوي)
{'arabic_name':'برلين – تيغل (مغلق سابقاً)','english_name':'Berlin Tegel (TXL)','country_code':'DEU','iata_code':'TXL','city_arabic':'برلين','city_english':'Berlin'},
{'arabic_name':'برلين – شانهبول/شتاينهوف','english_name':'Berlin Schönefeld (SXF)','country_code':'DEU','iata_code':'SXF','city_arabic':'برلين','city_english':'Berlin'},

# إيطاليا (ميلانو ثانوي)
{'arabic_name':'ميلانو – ليناتي','english_name':'Milan Linate (LIN)','country_code':'ITA','iata_code':'LIN','city_arabic':'ميلانو','city_english':'Milan'},
{'arabic_name':'ميلانو – أوريو ألبريلو','english_name':'Orio al Serio / Bergamo (BGY)','country_code':'ITA','iata_code':'BGY','city_arabic':'ميلانو','city_english':'Milan'},

# اليابان (طوكيو ثانوي)
{'arabic_name':'طوكيو – هانيدا','english_name':'Tokyo Haneda (HND)','country_code':'JPN','iata_code':'HND','city_arabic':'طوكيو','city_english':'Tokyo'},
{'arabic_name':'طوكيو – إيباراكي','english_name':'Ibaraki Airport (IBR)','country_code':'JPN','iata_code':'IBR','city_arabic':'طوكيو','city_english':'Tokyo'},
{'arabic_name':'طوكيو – تشوفو','english_name':'Chofu Airport (QBJ/CJH)','country_code':'JPN','iata_code':'CJH','city_arabic':'طوكيو','city_english':'Tokyo'},

# الصين (بكين، شنغهاي ثانوين)
{'arabic_name':'بكين – داشينغ','english_name':'Beijing Daxing (PKX)','country_code':'CHN','iata_code':'PKX','city_arabic':'بكين','city_english':'Beijing'},
{'arabic_name':'شنغهاي – هونغكياو','english_name':'Shanghai Hongqiao (SHA)','country_code':'CHN','iata_code':'SHA','city_arabic':'شنغهاي','city_english':'Shanghai'},
{'arabic_name':'شنغهاي – بودونغ','english_name':'Shanghai Pudong (PVG) (secondary)','country_code':'CHN','iata_code':'PVG','city_arabic':'شنغهاي','city_english':'Shanghai'},

# روسيا (موسكو ثانوين/أكثر)
{'arabic_name':'موسكو – دوموديدوفو','english_name':'Domodedovo (DME)','country_code':'RUS','iata_code':'DME','city_arabic':'موسكو','city_english':'Moscow'},
{'arabic_name':'موسكو – فنوكوفو','english_name':'Vnukovo (VKO)','country_code':'RUS','iata_code':'VKO','city_arabic':'موسكو','city_english':'Moscow'},
{'arabic_name':'موسكو – جوكوفسكي','english_name':'Zhukovsky (ZIA)','country_code':'RUS','iata_code':'ZIA','city_arabic':'موسكو','city_english':'Moscow'},
{'arabic_name':'موسكو – شيريميتيفو (ثانوي)','english_name':'Sheremetyevo (SVO)','country_code':'RUS','iata_code':'SVO','city_arabic':'موسكو','city_english':'Moscow'},

# كوريا (سيول ثانوين)
{'arabic_name':'سيول – قيمبو','english_name':'Gimpo (GMP)','country_code':'KOR','iata_code':'GMP','city_arabic':'سيول','city_english':'Seoul'},
{'arabic_name':'سيول – إنتشون','english_name':'Incheon (ICN)','country_code':'KOR','iata_code':'ICN','city_arabic':'سيول','city_english':'Seoul'},

# الفلبين (مانيلا ثانوي)
{'arabic_name':'مانيلا – كلارك','english_name':'Clark International (CRK)','country_code':'PHL','iata_code':'CRK','city_arabic':'مانيلا','city_english':'Manila'},

# تايلاند (بانكوك ثانوي)
{'arabic_name':'بانكوك – دون موانغ','english_name':'Don Mueang (DMK)','country_code':'THA','iata_code':'DMK','city_arabic':'بانكوك','city_english':'Bangkok'},
{'arabic_name':'بانكوك – SUVARNABHUMI','english_name':'Suvarnabhumi (BKK)','country_code':'THA','iata_code':'BKK','city_arabic':'بانكوك','city_english':'Bangkok'},

# الفلبين/إندونيسيا إضافات إقليمية
{'arabic_name':'جدة – مطار الأمير محمد بن عبدالعزيز (ثانوي إن وجد)','english_name':'Prince Mohammad bin Abdulaziz (MED)','country_code':'SAU','iata_code':'MED','city_arabic':'المدينة المنورة','city_english':'Medina'},

# هولندا (أمستردام ثانوي)
{'arabic_name':'أمستردام – سنتهيول','english_name':'Schiphol (AMS) (primary but listed)','country_code':'NLD','iata_code':'AMS','city_arabic':'أمستردام','city_english':'Amsterdam'},
{'arabic_name':'أمستردام – أيندهوفن (بديل إقليمي)','english_name':'Eindhoven (EIN)','country_code':'NLD','iata_code':'EIN','city_arabic':'أمستردام','city_english':'Amsterdam'},

# إسبانيا (مدريد وبرشلونة ثانوي)
{'arabic_name':'مدريد – باراخاس (MAD) (المطار الرئيسي لكن أضفت ثانويات)','english_name':'Adolfo Suárez Madrid–Barajas (MAD)','country_code':'ESP','iata_code':'MAD','city_arabic':'مدريد','city_english':'Madrid'},
{'arabic_name':'مدريد – خافيير','english_name':'Cuatro Vientos (secondary GA)','country_code':'ESP','iata_code':''},


# أستراليا (ملبورن ثانوي)
{'arabic_name':'ملبورن – أفالون','english_name':'Avalon (AVV)','country_code':'AUS','iata_code':'AVV','city_arabic':'ملبورن','city_english':'Melbourne'},
{'arabic_name':'ملبورن – مورابن','english_name':'Moorabbin (MBW)','country_code':'AUS','iata_code':'MBW','city_arabic':'ملبورن','city_english':'Melbourne'},

# نيوزيلندا (أوكلاند ثانوي)
{'arabic_name':'أوكلاند – ويلمینگتون (ثانوي)','english_name':'Wellington (WLG)','country_code':'NZL','iata_code':'WLG','city_arabic':'أوكلاند','city_english':'Auckland'},

# اليونان (أثينا ثانوي)
{'arabic_name':'أثينا – سكيابارس','english_name':'Skiathos (JSI)','country_code':'GRC','iata_code':'JSI','city_arabic':'أثينا','city_english':'Athens'},

# البرتغال (لشبونة ثانوي)
{'arabic_name':'لشبونة – كاشكايش (كازكايش طيران عام)','english_name':'Cascais (CAT)','country_code':'PRT','iata_code':'CAT','city_arabic':'لشبونة','city_english':'Lisbon'},

# بلدان وأمثلة إضافية مزدوجة (قائمة مختصرة، كل مطار ثانوي سطر)
{'arabic_name':'كولومبو – راتمالانا','english_name':'Ratmalana (RML)','country_code':'LKA','iata_code':'RML','city_arabic':'كولومبو','city_english':'Colombo'},
{'arabic_name':'نيروبي – ويلسون','english_name':'Wilson (WIL)','country_code':'KEN','iata_code':'WIL','city_arabic':'نيروبي','city_english':'Nairobi'},
{'arabic_name':'جوهانسبرغ – لانسيريا','english_name':'Lanseria (HLA)','country_code':'ZAF','iata_code':'HLA','city_arabic':'جوهانسبرغ','city_english':'Johannesburg'},
{'arabic_name':'كاسبلانكا – سابلغة (ثانوي)','english_name':'Nouasseur / Mohammed V (CMN)','country_code':'MAR','iata_code':'CMN','city_arabic':'الدار البيضاء','city_english':'Casablanca'},
{'arabic_name':'سيدني – بانكستاون/كمبرلاند (ثانوي)','english_name':'Bankstown (BWU)','country_code':'AUS','iata_code':'BWU','city_arabic':'سيدني','city_english':'Sydney'},
{'arabic_name':'فيينا – شوبنهافين (ثانوي)','english_name':'Schwechat (VIE)','country_code':'AUT','iata_code':'VIE','city_arabic':'فيينا','city_english':'Vienna'},

# مزيد من المدن المشهورة متعددة المطارات (ثانويات)
{'arabic_name':'ميلان – بيرغامو (Orio al Serio)','english_name':'Bergamo (BGY)','country_code':'ITA','iata_code':'BGY','city_arabic':'ميلانو','city_english':'Milan'},
{'arabic_name':'روما – تشامبينو','english_name':'Ciampino (CIA)','country_code':'ITA','iata_code':'CIA','city_arabic':'روما','city_english':'Rome'},
{'arabic_name':'نابولي – كابوديكينو','english_name':'Capodichino (NAP)','country_code':'ITA','iata_code':'NAP','city_arabic':'نابولي','city_english':'Naples'},

# هلسنكي ثانوي
{'arabic_name':'هلسنكي – واندربيرغ (ثانوي)','english_name':'Vantaa/secondary (alternative)','country_code':'FIN','iata_code':'HEL','city_arabic':'هلسنكي','city_english':'Helsinki'},

# المزيد من الأمثلة الشائعة (كل سطر = مطار ثانوي لمدينة معروفة)
{'arabic_name':'روتردام/لاهاي – ايه X (ثانوي)','english_name':'Rotterdam The Hague (RTM)','country_code':'NLD','iata_code':'RTM','city_arabic':'روتردام','city_english':'Rotterdam'},
{'arabic_name':'آمستردام – أيندهوفن','english_name':'Eindhoven (EIN)','country_code':'NLD','iata_code':'EIN','city_arabic':'أمستردام','city_english':'Amsterdam'},
{'arabic_name':'بكين – شيجياتشوانغ/تشونغتشينغ (ثانوي)','english_name':'(regional secondaries)','country_code':'CHN','iata_code':''},
{'arabic_name':'شنجن – شينزين (ثانوي)','english_name':'Shenzhen (SZX)','country_code':'CHN','iata_code':'SZX','city_arabic':'شنجن','city_english':'Shenzhen'},

# المدن الأمريكية الإقليمية ذات مطارات إضافية (مختارة)
{'arabic_name':'بافالو – نياجرا فولز','english_name':'Niagara Falls Intl (IAG)','country_code':'USA','iata_code':'IAG','city_arabic':'بافالو','city_english':'Buffalo'},
{'arabic_name':'شارلوت – مترو/كونكورد (ثانوي)','english_name':'Concord (JQF)','country_code':'USA','iata_code':'JQF','city_arabic':'شارلوت','city_english':'Charlotte'},

# أمريكا الجنوبية - مدن ثانوية
{'arabic_name':'سانتياغو – تيرمينال إقتصادي (ثانوي)','english_name':'Santiago (others)','country_code':'CHL','iata_code':'SCL','city_arabic':'سانتياغو','city_english':'Santiago'},
{'arabic_name':'بوينس آيرس – إلدورو (ثانوي)','english_name':'El Palomar (EPA)','country_code':'ARG','iata_code':'EPA','city_arabic':'بوينس آيرس','city_english':'Buenos Aires'},

# الشرق الأوسط - أمثلة ثانوية
{'arabic_name':'إسطنبول – صبيحة جوكتشن','english_name':'Sabiha Gokcen (SAW)','country_code':'TUR','iata_code':'SAW','city_arabic':'إسطنبول','city_english':'Istanbul'},
{'arabic_name':'الدار البيضاء – سطنّة/ثانوي','english_name':'Safi (regional)','country_code':'MAR','iata_code':''},

# بقية الأمثلة المتفرقة (قائمة تغطي مدناً عديدة)
{'arabic_name':'سان خوان – تيرمينال آخر','english_name':'Isla Grande (SIG)','country_code':'PRI','iata_code':'SIG','city_arabic':'سان خوان','city_english':'San Juan'},
{'arabic_name':'بكين – العاصمة / داشينغ','english_name':'Beijing Daxing (PKX)','country_code':'CHN','iata_code':'PKX','city_arabic':'بكين','city_english':'Beijing'},
{'arabic_name':'طوكيو – ناريتا','english_name':'Narita (NRT)','country_code':'JPN','iata_code':'NRT','city_arabic':'طوكيو','city_english':'Tokyo'}


        ]
        
        for city_data in cities_data:
            if not City.query.filter_by(iata_code=city_data['iata_code']).first():
                country = Country.query.filter_by(country_code=city_data['country_code']).first()
                if country:
                    city = City(
                        arabic_name=city_data['arabic_name'],
                        english_name=city_data['english_name'],
                        iata_code=city_data['iata_code'],
                        country_id=country.id
                    )
                    db.session.add(city)
                    print(f"تم إضافة مدينة: {city_data['arabic_name']}")
        

                # إضافة شركات الطيران العربية والدولية
        airlines_data = [
                    # شركات الطيران السعودية
                    
                    {'arabic_name': 'الخطوط الجوية العربية السعودية','english_name': 'Saudia','iata_code': 'SV','icao_code': 'SVA','country_code': 'SAU'},
                    {'arabic_name': 'ناس للطيران','english_name': 'Flynas','iata_code': 'XY','icao_code': 'KNE','country_code': 'SAU'},
                    {'arabic_name': 'مصر للطيران','english_name': 'EgyptAir','iata_code': 'MS','icao_code': 'MSR','country_code': 'EGY'},
                    {'arabic_name': 'طيران النيل','english_name': 'Nile Air','iata_code': 'NP','icao_code': 'NLF','country_code': 'EGY'},
                    {'arabic_name': 'الخطوط الجوية الإماراتية','english_name': 'Emirates','iata_code': 'EK','icao_code': 'UAE','country_code': 'ARE'},
                    {'arabic_name': 'الاتحاد للطيران','english_name': 'Etihad Airways','iata_code': 'EY','icao_code': 'ETD','country_code': 'ARE'},
                    {'arabic_name': 'فلاي دبي','english_name': 'Flydubai','iata_code': 'FZ','icao_code': 'FDB','country_code': 'ARE'},
                    {'arabic_name': 'الخطوط الجوية القطرية','english_name': 'Qatar Airways','iata_code': 'QR','icao_code': 'QTR','country_code': 'QAT'},
                    {'arabic_name': 'الخطوط الجوية العمانية','english_name': 'Oman Air','iata_code': 'WY','icao_code': 'OMA','country_code': 'OMN'},
                    {'arabic_name': 'الخطوط الجوية البحرينية','english_name': 'Gulf Air','iata_code': 'GF','icao_code': 'GFA','country_code': 'BHR'},
                    {'arabic_name': 'الخطوط الجوية الكويتية','english_name': 'Kuwait Airways','iata_code': 'KU','icao_code': 'KAC','country_code': 'KWT'},
                    {'arabic_name': 'الخطوط الأردنية','english_name': 'Royal Jordanian','iata_code': 'RJ','icao_code': 'RJA','country_code': 'JOR'},
                    {'arabic_name': 'الخطوط الجوية اللبنانية','english_name': 'Middle East Airlines','iata_code': 'ME','icao_code': 'MEA','country_code': 'LBN'},
                    {'arabic_name': 'الخطوط الجوية العراقية','english_name': 'Iraqi Airways','iata_code': 'IA','icao_code': 'IAW','country_code': 'IRQ'},
                    {'arabic_name': 'طيران اليمنية','english_name': 'Yemenia','iata_code': 'IY','icao_code': 'YIA','country_code': 'YEM'},
                    {'arabic_name': 'طيران ليبيا','english_name': 'Libyan Airlines','iata_code': 'LN','icao_code': 'LBY','country_code': 'LBY'},
                    {'arabic_name': 'الخطوط الجوية السودانية','english_name': 'Sudan Airways','iata_code': 'SD','icao_code': 'SUD','country_code': 'SDN'},
                    {'arabic_name': 'طيران الجزائر','english_name': 'Air Algérie','iata_code': 'AH','icao_code': 'DAH','country_code': 'DZA'},
                    {'arabic_name': 'الخطوط الجوية المغربية','english_name': 'Royal Air Maroc','iata_code': 'AT','icao_code': 'RAM','country_code': 'MAR'},
                    {'arabic_name': 'الخطوط التونسية','english_name': 'Tunisair','iata_code': 'TU','icao_code': 'TAR','country_code': 'TUN'},

                    {'arabic_name': 'الخطوط الجوية الصينية','english_name': 'Air China','iata_code': 'CA','icao_code': 'CCA','country_code': 'CHN'},
                    {'arabic_name': 'الخطوط الجوية الشرقية الصينية','english_name': 'China Eastern','iata_code': 'MU','icao_code': 'CES','country_code': 'CHN'},
                    {'arabic_name': 'الخطوط الجوية الجنوبية الصينية','english_name': 'China Southern','iata_code': 'CZ','icao_code': 'CSN','country_code': 'CHN'},
                    {'arabic_name': 'الخطوط الجوية اليابانية','english_name': 'Japan Airlines','iata_code': 'JL','icao_code': 'JAL','country_code': 'JPN'},
                    {'arabic_name': 'آل نيبون','english_name': 'All Nippon Airways','iata_code': 'NH','icao_code': 'ANA','country_code': 'JPN'},
                    {'arabic_name': 'الخطوط الجوية الهندية','english_name': 'Air India','iata_code': 'AI','icao_code': 'AIC','country_code': 'IND'},
                    {'arabic_name': 'إنديجو','english_name': 'IndiGo','iata_code': '6E','icao_code': 'IGO','country_code': 'IND'},
                    {'arabic_name': 'سنغافورة إيرلاينز','english_name': 'Singapore Airlines','iata_code': 'SQ','icao_code': 'SIA','country_code': 'SGP'},
                    {'arabic_name': 'الخطوط التايلاندية','english_name': 'Thai Airways','iata_code': 'TG','icao_code': 'THA','country_code': 'THA'},
                    {'arabic_name': 'ماليزيا إيرلاينز','english_name': 'Malaysia Airlines','iata_code': 'MH','icao_code': 'MAS','country_code': 'MYS'},
                    {'arabic_name': 'جارودا إندونيسيا','english_name': 'Garuda Indonesia','iata_code': 'GA','icao_code': 'GIA','country_code': 'IDN'},
                    {'arabic_name': 'الخطوط الجوية الفيتنامية','english_name': 'Vietnam Airlines','iata_code': 'VN','icao_code': 'HVN','country_code': 'VNM'},
                    {'arabic_name': 'فيليبيني إيرلاينز','english_name': 'Philippine Airlines','iata_code': 'PR','icao_code': 'PAL','country_code': 'PHL'},
                    {'arabic_name': 'الخطوط الجوية الكورية','english_name': 'Korean Air','iata_code': 'KE','icao_code': 'KAL','country_code': 'KOR'},
                    {'arabic_name': 'آسيا إير','english_name': 'Asiana Airlines','iata_code': 'OZ','icao_code': 'AAR','country_code': 'KOR'},
                    {'arabic_name': 'تركش إيرلاينز','english_name': 'Turkish Airlines','iata_code': 'TK','icao_code': 'THY','country_code': 'TUR'},
                    {'arabic_name': 'الخطوط الجوية الإسرائيلية','english_name': 'El Al','iata_code': 'LY','icao_code': 'ELY','country_code': 'ISR'},
                    {'arabic_name': 'الخطوط الباكستانية','english_name': 'Pakistan International Airlines','iata_code': 'PK','icao_code': 'PIA','country_code': 'PAK'},
                    {'arabic_name': 'طيران سريلانكا','english_name': 'SriLankan Airlines','iata_code': 'UL','icao_code': 'ALK','country_code': 'LKA'},
                    {'arabic_name': 'الخطوط الجوية البنغلاديشية','english_name': 'Biman Bangladesh','iata_code': 'BG','icao_code': 'BBC','country_code': 'BGD'},
                    {'arabic_name': 'الخطوط النيبالية','english_name': 'Nepal Airlines','iata_code': 'RA','icao_code': 'RNA','country_code': 'NPL'},
                    {'arabic_name': 'إيفا إير','english_name': 'EVA Air','iata_code': 'BR','icao_code': 'EVA','country_code': 'TWN'},
                    {'arabic_name': 'الخطوط الجوية التايوانية','english_name': 'China Airlines','iata_code': 'CI','icao_code': 'CAL','country_code': 'TWN'},
                    {'arabic_name': 'الخطوط الجوية لهونغ كونغ','english_name': 'Cathay Pacific','iata_code': 'CX','icao_code': 'CPA','country_code': 'HKG'},
                    {'arabic_name': 'الخطوط الجوية الكازاخستانية','english_name': 'Air Astana','iata_code': 'KC','icao_code': 'KZR','country_code': 'KAZ'},
                    {'arabic_name': 'أذربيجان إيرلاينز','english_name': 'Azerbaijan Airlines','iata_code': 'J2','icao_code': 'AHY','country_code': 'AZE'},
                    {'arabic_name': 'أوزبكستان هافا يوللاري','english_name': 'Uzbekistan Airways','iata_code': 'HY','icao_code': 'UZB','country_code': 'UZB'},
                    {'arabic_name': 'جورجيا إيرلاينز','english_name': 'Georgian Airways','iata_code': 'A9','icao_code': 'GGY','country_code': 'GEO'},

                    
                    {'arabic_name': 'الخطوط الجوية البريطانية','english_name': 'British Airways','iata_code': 'BA','icao_code': 'BAW','country_code': 'GBR'},
                    {'arabic_name': 'إيزي جت','english_name': 'easyJet','iata_code': 'U2','icao_code': 'EZY','country_code': 'GBR'},
                    {'arabic_name': 'الخطوط الفرنسية','english_name': 'Air France','iata_code': 'AF','icao_code': 'AFR','country_code': 'FRA'},
                    {'arabic_name': 'لوفتهانزا','english_name': 'Lufthansa','iata_code': 'LH','icao_code': 'DLH','country_code': 'DEU'},
                    {'arabic_name': 'إير برلين','english_name': 'Air Berlin','iata_code': 'AB','icao_code': 'BER','country_code': 'DEU'},
                    {'arabic_name': 'إيبيريا','english_name': 'Iberia','iata_code': 'IB','icao_code': 'IBE','country_code': 'ESP'},
                    {'arabic_name': 'فولانديش إيرلاينز','english_name': 'Vueling','iata_code': 'VY','icao_code': 'VLG','country_code': 'ESP'},
                    {'arabic_name': 'الخطوط الجوية الإيطالية','english_name': 'Alitalia','iata_code': 'AZ','icao_code': 'AZA','country_code': 'ITA'},
                    {'arabic_name': 'إير لينغوس','english_name': 'Aer Lingus','iata_code': 'EI','icao_code': 'EIN','country_code': 'IRL'},
                    {'arabic_name': 'كي إل إم','english_name': 'KLM Royal Dutch Airlines','iata_code': 'KL','icao_code': 'KLM','country_code': 'NLD'},
                    {'arabic_name': 'سويز إير','english_name': 'Swiss International Air Lines','iata_code': 'LX','icao_code': 'SWR','country_code': 'CHE'},
                    {'arabic_name': 'أوستريا إيرلاينز','english_name': 'Austrian Airlines','iata_code': 'OS','icao_code': 'AUA','country_code': 'AUT'},
                    {'arabic_name': 'ساينس إير','english_name': 'SAS Scandinavian Airlines','iata_code': 'SK','icao_code': 'SAS','country_code': 'SWE'},
                    {'arabic_name': 'نورويجيان إير','english_name': 'Norwegian Air Shuttle','iata_code': 'DY','icao_code': 'NAX','country_code': 'NOR'},
                    {'arabic_name': 'فين إير','english_name': 'Finnair','iata_code': 'AY','icao_code': 'FIN','country_code': 'FIN'},
                    {'arabic_name': 'آير موسكو','english_name': 'Aeroflot','iata_code': 'SU','icao_code': 'AFL','country_code': 'RUS'},
                    {'arabic_name': 'بولندا إيرلاينز','english_name': 'LOT Polish Airlines','iata_code': 'LO','icao_code': 'LOT','country_code': 'POL'},
                    {'arabic_name': 'ترانسافيا','english_name': 'Transavia','iata_code': 'HV','icao_code': 'TRA','country_code': 'NLD'},
                    {'arabic_name': 'براغ إيرلاينز','english_name': 'Czech Airlines','iata_code': 'OK','icao_code': 'CSA','country_code': 'CZE'},
                    {'arabic_name': 'ماغيار إيرلاينز','english_name': 'Wizz Air','iata_code': 'W6','icao_code': 'WZZ','country_code': 'HUN'},
                    {'arabic_name': 'أثينا إير','english_name': 'Aegean Airlines','iata_code': 'A3','icao_code': 'AEE','country_code': 'GRC'},
                    {'arabic_name': 'توبورغ إير','english_name': 'TAP Air Portugal','iata_code': 'TP','icao_code': 'TAP','country_code': 'PRT'},
                    {'arabic_name': 'إير بروكسل','english_name': 'Brussels Airlines','iata_code': 'SN','icao_code': 'BEL','country_code': 'BEL'},
                    {'arabic_name': 'ريكيافيك إير','english_name': 'Icelandair','iata_code': 'FI','icao_code': 'ICE','country_code': 'ISL'},
                    {'arabic_name': 'بوخارست إير','english_name': 'Tarom','iata_code': 'RO','icao_code': 'ROT','country_code': 'ROU'},

                                        
                    # 🇺🇸 الولايات المتحدة
                    {'arabic_name': 'أمريكان إيرلاينز','english_name': 'American Airlines','iata_code': 'AA','icao_code': 'AAL','country_code': 'USA'},
                    {'arabic_name': 'دلتا إيرلاينز','english_name': 'Delta Air Lines','iata_code': 'DL','icao_code': 'DAL','country_code': 'USA'},
                    {'arabic_name': 'يونايتد إيرلاينز','english_name': 'United Airlines','iata_code': 'UA','icao_code': 'UAL','country_code': 'USA'},
                    {'arabic_name': 'ساوثويست إيرلاينز','english_name': 'Southwest Airlines','iata_code': 'WN','icao_code': 'SWA','country_code': 'USA'},
                    {'arabic_name': 'ألاسكا إيرلاينز','english_name': 'Alaska Airlines','iata_code': 'AS','icao_code': 'ASA','country_code': 'USA'},

                    # 🇨🇦 كندا
                    {'arabic_name': 'إير كندا','english_name': 'Air Canada','iata_code': 'AC','icao_code': 'ACA','country_code': 'CAN'},
                    {'arabic_name': 'ويست جيت','english_name': 'WestJet','iata_code': 'WS','icao_code': 'WJA','country_code': 'CAN'},

                    # 🇲🇽 المكسيك
                    {'arabic_name': 'إيرومكس','english_name': 'Aeromexico','iata_code': 'AM','icao_code': 'AMX','country_code': 'MEX'},
                    {'arabic_name': 'فولكانو إير','english_name': 'Volaris','iata_code': 'Y4','icao_code': 'VOI','country_code': 'MEX'},

                    # 🇧🇷 البرازيل
                    {'arabic_name': 'جازيلا إير','english_name': 'GOL Linhas Aéreas','iata_code': 'G3','icao_code': 'GLO','country_code': 'BRA'},
                    {'arabic_name': 'تام إيرلاينز','english_name': 'LATAM Airlines Brazil','iata_code': 'JJ','icao_code': 'TAM','country_code': 'BRA'},

                    # 🇦🇷 الأرجنتين
                    {'arabic_name': 'أيرو ليناس الأرجنتينية','english_name': 'Aerolineas Argentinas','iata_code': 'AR','icao_code': 'ARG','country_code': 'ARG'},

                    # 🇨🇱 تشيلي
                    {'arabic_name': 'لان تشيلي','english_name': 'LATAM Airlines Chile','iata_code': 'LA','icao_code': 'LAN','country_code': 'CHL'},

                    # 🇨🇴 كولومبيا
                    {'arabic_name': 'أفيانكا','english_name': 'Avianca','iata_code': 'AV','icao_code': 'AVA','country_code': 'COL'},

                    # 🇵🇪 بيرو
                    {'arabic_name': 'لاطام بيرو','english_name': 'LATAM Airlines Peru','iata_code': 'LP','icao_code': 'LAP','country_code': 'PER'},

                    # 🇦🇺 أستراليا
                    {'arabic_name': 'كانتاس','english_name': 'Qantas','iata_code': 'QF','icao_code': 'QFA','country_code': 'AUS'},
                    {'arabic_name': 'فيرست إيرلاينز الأسترالية','english_name': 'Virgin Australia','iata_code': 'VA','icao_code': 'VOZ','country_code': 'AUS'},

                    # 🇳🇿 نيوزيلندا
                    {'arabic_name': 'إير نيوزيلندا','english_name': 'Air New Zealand','iata_code': 'NZ','icao_code': 'ANZ','country_code': 'NZL'}

                    



                ]
                
        for airline_data in airlines_data:
                    if not Airline.query.filter_by(iata_code=airline_data['iata_code']).first():
                        country = Country.query.filter_by(country_code=airline_data['country_code']).first()
                        if country:
                            airline = Airline(
                                arabic_name=airline_data['arabic_name'],
                                english_name=airline_data['english_name'],
                                iata_code=airline_data['iata_code'],
                                icao_code=airline_data['icao_code'],
                                country_id=country.id
                            )
                            db.session.add(airline)
                            print(f"✅ تم إضافة شركة طيران: {airline_data['arabic_name']} ({airline_data['iata_code']})")
                        else:
                            print(f"⚠️  تحذير: الدولة {airline_data['country_code']} غير موجودة لشركة الطيران {airline_data['arabic_name']}")


        text_replacements_data = [
    {'original_text': 'إلى', 'replacement_text': 'الى', 'description': 'إزالة الهمزة'},
    {'original_text': 'أ', 'replacement_text': 'ا', 'description': 'استبدال الهمزة'},
    {'original_text': 'إ', 'replacement_text': 'ا', 'description': 'استبدال الهمزة'},
    {'original_text': 'آ', 'replacement_text': 'ا', 'description': 'استبدال الهمزة'},
    {'original_text': 'ة', 'replacement_text': 'ه', 'description': 'استبدال التاء المربوطة'},
    {'original_text': 'ـ', 'replacement_text': '', 'description': 'إزالة التطويل'},
    {'original_text': 'ّ', 'replacement_text': '', 'description': 'إزالة الشدة'},
    {'original_text': 'َ', 'replacement_text': '', 'description': 'إزالة الفتحة'},
    {'original_text': 'ُ', 'replacement_text': '', 'description': 'إزالة الضمة'},
    {'original_text': 'ِ', 'replacement_text': '', 'description': 'إزالة الكسرة'},
    {'original_text': 'ْ', 'replacement_text': '', 'description': 'إزالة السكون'},
    {'original_text': 'بكرا', 'replacement_text': 'غدا', 'description': 'مرادف عامي'},
    {'original_text': 'غداً', 'replacement_text': 'غدا', 'description': 'إزالة التشكيل'},
]

        

        for tr in text_replacements_data:
            existing = ArabicTextReplacement.query.filter_by(original_text=tr['original_text']).first()

            if not existing:
                text_rep = ArabicTextReplacement(
                    original_text=tr['original_text'],
                    replacement_text=tr['replacement_text'],
                    description=tr.get('description', '')
                )
                db.session.add(text_rep)

                print(f"✅ تم إضافة استبدال: {tr['original_text']} ➝ {tr['replacement_text']}")
            else:
                print(f"⚠️ موجود مسبقًا: {tr['original_text']} — لم يتم الإضافة")



                            
        # حفظ التغييرات
        db.session.commit()
        print("✅ تم إنشاء الجداول وإضافة البيانات الأولية بنجاح!")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ حدث خطأ أثناء إضافة البيانات الأولية: {str(e)}")