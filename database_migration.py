# database_migration.py
from flask import Flask
from models import db, ArabicCity, EnglishCity, ArabicMonth, ArabicTextReplacement, Airline, UserQueryPattern, SystemSettings, NLPProcessingLog, CityAlias, SearchHistory
from datetime import datetime
import shutil
import os

def upgrade_database(app):
    """ترقية قاعدة البيانات لإضافة الحقول الجديدة"""
    with app.app_context():
        try:
            # تنفيذ أوامر SQL لإضافة الحقول المفقودة
            from sqlalchemy import text
            
            # تحديث جدول arabic_cities
            try:
                db.session.execute(text('''
                    ALTER TABLE arabic_cities 
                    ADD COLUMN country_arabic VARCHAR(100),
                    ADD COLUMN country_english VARCHAR(100),
                    ADD COLUMN timezone VARCHAR(50),
                    ADD COLUMN is_popular BOOLEAN DEFAULT FALSE,
                    ADD COLUMN popularity_score INTEGER DEFAULT 0,
                    ADD COLUMN alternative_names TEXT,
                    ADD COLUMN latitude FLOAT,
                    ADD COLUMN longitude FLOAT,
                    ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                '''))
                print("✅ تم تحديث جدول arabic_cities")
            except Exception as e:
                print(f"⚠️ حقل موجود مسبقاً في arabic_cities: {e}")
            
            # تحديث جدول english_cities
            try:
                db.session.execute(text('''
                    ALTER TABLE english_cities 
                    ADD COLUMN country_arabic VARCHAR(100),
                    ADD COLUMN country_english VARCHAR(100),
                    ADD COLUMN timezone VARCHAR(50),
                    ADD COLUMN is_popular BOOLEAN DEFAULT FALSE,
                    ADD COLUMN popularity_score INTEGER DEFAULT 0,
                    ADD COLUMN alternative_names TEXT,
                    ADD COLUMN latitude FLOAT,
                    ADD COLUMN longitude FLOAT,
                    ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                '''))
                print("✅ تم تحديث جدول english_cities")
            except Exception as e:
                print(f"⚠️ حقل موجود مسبقاً في english_cities: {e}")
            
            # تحديث جدول arabic_months
            try:
                db.session.execute(text('''
                    ALTER TABLE arabic_months 
                    ADD COLUMN alternative_names TEXT
                '''))
                print("✅ تم تحديث جدول arabic_months")
            except Exception as e:
                print(f"⚠️ حقل موجود مسبقاً في arabic_months: {e}")
            
            # تحديث جدول arabic_text_replacements
            try:
                db.session.execute(text('''
                    ALTER TABLE arabic_text_replacements 
                    ADD COLUMN replacement_type VARCHAR(20) DEFAULT 'normalization',
                    ADD COLUMN priority INTEGER DEFAULT 5
                '''))
                print("✅ تم تحديث جدول arabic_text_replacements")
            except Exception as e:
                print(f"⚠️ حقل موجود مسبقاً في arabic_text_replacements: {e}")
            
            # تحديث جدول airlines
            try:
                db.session.execute(text('''
                    ALTER TABLE airlines 
                    ADD COLUMN country_arabic VARCHAR(100),
                    ADD COLUMN is_popular BOOLEAN DEFAULT FALSE,
                    ADD COLUMN alternative_names TEXT,
                    ADD COLUMN logo_url VARCHAR(255),
                    ADD COLUMN website VARCHAR(255),
                    ADD COLUMN contact_number VARCHAR(50),
                    ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                '''))
                print("✅ تم تحديث جدول airlines")
            except Exception as e:
                print(f"⚠️ حقل موجود مسبقاً في airlines: {e}")
            
            # تحديث جدول search_history
            try:
                db.session.execute(text('''
                    ALTER TABLE search_history 
                    ADD COLUMN adults INTEGER DEFAULT 1,
                    ADD COLUMN children INTEGER DEFAULT 0,
                    ADD COLUMN infants INTEGER DEFAULT 0,
                    ADD COLUMN airline_preference VARCHAR(10),
                    ADD COLUMN search_type VARCHAR(20) DEFAULT 'one_way',
                    ADD COLUMN is_lowest_price_search BOOLEAN DEFAULT FALSE
                '''))
                print("✅ تم تحديث جدول search_history")
            except Exception as e:
                print(f"⚠️ حقل موجود مسبقاً في search_history: {e}")
            
            # إنشاء الجداول الجديدة إذا لم تكن موجودة
            db.create_all()
            
            # تحديث البيانات الافتراضية
            update_default_data(app)
            
            db.session.commit()
            print("🎉 تم ترقية قاعدة البيانات بنجاح!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ خطأ في ترقية قاعدة البيانات: {e}")

def update_default_data(app):
    """تحديث البيانات الافتراضية"""
    with app.app_context():
        try:
            # تحديث بيانات المدن العربية
            arabic_cities_updates = {
                'الرياض': {
                    'country_arabic': 'المملكة العربية السعودية',
                    'country_english': 'Saudi Arabia',
                    'timezone': 'Asia/Riyadh',
                    'is_popular': True,
                    'popularity_score': 100,
                    'alternative_names': 'العارض,الخرج,الدرعية',
                    'latitude': 24.7136,
                    'longitude': 46.6753
                },
                'جدة': {
                    'country_arabic': 'المملكة العربية السعودية',
                    'country_english': 'Saudi Arabia',
                    'timezone': 'Asia/Riyadh',
                    'is_popular': True,
                    'popularity_score': 95,
                    'alternative_names': 'جده,ميناء جدة',
                    'latitude': 21.4858,
                    'longitude': 39.1925
                },
                'دمام': {
                    'country_arabic': 'المملكة العربية السعودية',
                    'country_english': 'Saudi Arabia',
                    'timezone': 'Asia/Riyadh',
                    'is_popular': True,
                    'popularity_score': 90,
                    'alternative_names': 'الدمام,المنطقة الشرقية',
                    'latitude': 26.3927,
                    'longitude': 49.9777
                },
                'دبي': {
                    'country_arabic': 'الإمارات العربية المتحدة',
                    'country_english': 'United Arab Emirates',
                    'timezone': 'Asia/Dubai',
                    'is_popular': True,
                    'popularity_score': 98,
                    'alternative_names': 'دبي,دبى,دبي المدينة',
                    'latitude': 25.2048,
                    'longitude': 55.2708
                },
                'أبوظبي': {
                    'country_arabic': 'الإمارات العربية المتحدة',
                    'country_english': 'United Arab Emirates',
                    'timezone': 'Asia/Dubai',
                    'is_popular': True,
                    'popularity_score': 85,
                    'alternative_names': 'ابوظبي,أبو ظبي,العاصمة الاتحادية',
                    'latitude': 24.4539,
                    'longitude': 54.3773
                },
                'الدوحة': {
                    'country_arabic': 'قطر',
                    'country_english': 'Qatar',
                    'timezone': 'Asia/Qatar',
                    'is_popular': True,
                    'popularity_score': 80,
                    'alternative_names': 'الدوحه,عاصمة قطر',
                    'latitude': 25.2854,
                    'longitude': 51.5310
                },
                'القاهرة': {
                    'country_arabic': 'مصر',
                    'country_english': 'Egypt',
                    'timezone': 'Africa/Cairo',
                    'is_popular': True,
                    'popularity_score': 92,
                    'alternative_names': 'القاهره,عاصمة مصر,مدينة القاهرة',
                    'latitude': 30.0444,
                    'longitude': 31.2357
                },
                'عمّان': {
                    'country_arabic': 'الأردن',
                    'country_english': 'Jordan',
                    'timezone': 'Asia/Amman',
                    'is_popular': True,
                    'popularity_score': 75,
                    'alternative_names': 'عمان,العاصمة الأردنية,عمان المدينة',
                    'latitude': 31.9539,
                    'longitude': 35.9106
                },
                'اسطنبول': {
                    'country_arabic': 'تركيا',
                    'country_english': 'Turkey',
                    'timezone': 'Europe/Istanbul',
                    'is_popular': True,
                    'popularity_score': 88,
                    'alternative_names': 'استنبول,القسطنطينية,إسطنبول',
                    'latitude': 41.0082,
                    'longitude': 28.9784
                }
            }
            
            for city_name, updates in arabic_cities_updates.items():
                city = ArabicCity.query.filter_by(arabic_name=city_name).first()
                if city:
                    for key, value in updates.items():
                        setattr(city, key, value)
            
            # تحديث بيانات المدن الإنجليزية
            english_cities_updates = {
                'riyadh': {
                    'country_arabic': 'المملكة العربية السعودية',
                    'country_english': 'Saudi Arabia',
                    'timezone': 'Asia/Riyadh',
                    'is_popular': True,
                    'popularity_score': 100,
                    'alternative_names': 'riyad,aryadh',
                    'latitude': 24.7136,
                    'longitude': 46.6753
                },
                'jeddah': {
                    'country_arabic': 'المملكة العربية السعودية',
                    'country_english': 'Saudi Arabia',
                    'timezone': 'Asia/Riyadh',
                    'is_popular': True,
                    'popularity_score': 95,
                    'alternative_names': 'jedda,gidda',
                    'latitude': 21.4858,
                    'longitude': 39.1925
                },
                'dammam': {
                    'country_arabic': 'المملكة العربية السعودية',
                    'country_english': 'Saudi Arabia',
                    'timezone': 'Asia/Riyadh',
                    'is_popular': True,
                    'popularity_score': 90,
                    'alternative_names': 'ad dammam,dammam city',
                    'latitude': 26.3927,
                    'longitude': 49.9777
                },
                'dubai': {
                    'country_arabic': 'الإمارات العربية المتحدة',
                    'country_english': 'United Arab Emirates',
                    'timezone': 'Asia/Dubai',
                    'is_popular': True,
                    'popularity_score': 98,
                    'alternative_names': 'duby,dubayy',
                    'latitude': 25.2048,
                    'longitude': 55.2708
                },
                'cairo': {
                    'country_arabic': 'مصر',
                    'country_english': 'Egypt',
                    'timezone': 'Africa/Cairo',
                    'is_popular': True,
                    'popularity_score': 92,
                    'alternative_names': 'al qahira,misr',
                    'latitude': 30.0444,
                    'longitude': 31.2357
                },
                'amman': {
                    'country_arabic': 'الأردن',
                    'country_english': 'Jordan',
                    'timezone': 'Asia/Amman',
                    'is_popular': True,
                    'popularity_score': 75,
                    'alternative_names': 'ammon,philadelphia',
                    'latitude': 31.9539,
                    'longitude': 35.9106
                }
            }
            
            for city_name, updates in english_cities_updates.items():
                city = EnglishCity.query.filter_by(english_name=city_name).first()
                if city:
                    for key, value in updates.items():
                        setattr(city, key, value)
            
            # تحديث بيانات الأشهر العربية
            months_updates = {
                'يناير': ['كانون الثاني', 'يناير', 'January'],
                'فبراير': ['شباط', 'فبراير', 'February'],
                'مارس': ['آذار', 'مارس', 'March'],
                'ابريل': ['نيسان', 'ابريل', 'April'],
                'مايو': ['أيار', 'مايو', 'May'],
                'يونيو': ['حزيران', 'يونيو', 'June'],
                'يوليو': ['تموز', 'يوليو', 'July'],
                'اغسطس': ['آب', 'اغسطس', 'August'],
                'سبتمبر': ['أيلول', 'سبتمبر', 'September'],
                'اكتوبر': ['تشرين الأول', 'اكتوبر', 'October'],
                'نوفمبر': ['تشرين الثاني', 'نوفمبر', 'November'],
                'ديسمبر': ['كانون الأول', 'ديسمبر', 'December']
            }
            
            for month_name, alternatives in months_updates.items():
                month = ArabicMonth.query.filter_by(arabic_name=month_name).first()
                if month:
                    month.alternative_names = ','.join(alternatives)
            
            # تحديث بيانات شركات الطيران
            airlines_updates = {
                'EK': {
                    'country_arabic': 'الإمارات العربية المتحدة',
                    'is_popular': True,
                    'alternative_names': 'الإمارات,طيران الإمارات,emirates airline',
                    'logo_url': 'https://example.com/emirates.png',
                    'website': 'https://www.emirates.com',
                    'contact_number': '+971600555555'
                },
                'QR': {
                    'country_arabic': 'قطر',
                    'is_popular': True,
                    'alternative_names': 'القطرية,الخطوط القطرية,qatar airline',
                    'logo_url': 'https://example.com/qatar.png',
                    'website': 'https://www.qatarairways.com',
                    'contact_number': '+97440230000'
                },
                'SV': {
                    'country_arabic': 'المملكة العربية السعودية',
                    'is_popular': True,
                    'alternative_names': 'السعودية,الخطوط السعودية,saudia airline',
                    'logo_url': 'https://example.com/saudia.png',
                    'website': 'https://www.saudia.com',
                    'contact_number': '+966920022222'
                },
                'EY': {
                    'country_arabic': 'الإمارات العربية المتحدة',
                    'is_popular': True,
                    'alternative_names': 'الاتحاد,طيران الاتحاد,etihad airline',
                    'logo_url': 'https://example.com/etihad.png',
                    'website': 'https://www.etihad.com',
                    'contact_number': '+971600555666'
                },
                'TK': {
                    'country_arabic': 'تركيا',
                    'is_popular': True,
                    'alternative_names': 'التركية,الخطوط التركية,turkish airline',
                    'logo_url': 'https://example.com/turkish.png',
                    'website': 'https://www.turkishairlines.com',
                    'contact_number': '+902124444084'
                },
                'RJ': {
                    'country_arabic': 'الأردن',
                    'is_popular': True,
                    'alternative_names': 'الأردنية,الخطوط الأردنية,royal jordanian',
                    'logo_url': 'https://example.com/rj.png',
                    'website': 'https://www.rj.com',
                    'contact_number': '+96265000000'
                }
            }
            
            for iata_code, updates in airlines_updates.items():
                airline = Airline.query.filter_by(iata_code=iata_code).first()
                if airline:
                    for key, value in updates.items():
                        setattr(airline, key, value)
            
            # إضافة مدن جديدة
            new_arabic_cities = [
                ('الصين', 'PEK', 'الصين', 'China', 'Asia/Shanghai', True, 70, 'الصين الشعبية,جمهورية الصين', 39.9042, 116.4074),
                ('دلهي', 'DEL', 'الهند', 'India', 'Asia/Kolkata', True, 65, 'دلهي الجديدة,عاصمة الهند', 28.6139, 77.2090),
                ('هانغزو', 'HGH', 'الصين', 'China', 'Asia/Shanghai', False, 50, 'هانغتشو,هانزو', 30.2741, 120.1551),
                ('غوانزو', 'CAN', 'الصين', 'China', 'Asia/Shanghai', False, 55, 'قوانغتشو,كانتون', 23.1291, 113.2644),
                ('الخرطوم', 'KRT', 'السودان', 'Sudan', 'Africa/Khartoum', False, 40, 'عاصمة السودان', 15.5007, 32.5599),
                ('الدار البيضاء', 'CMN', 'المغرب', 'Morocco', 'Africa/Casablanca', False, 45, 'كازابلانكا,دار البيضاء', 33.5731, -7.5898)
            ]
            
            for city_data in new_arabic_cities:
                if not ArabicCity.query.filter_by(arabic_name=city_data[0]).first():
                    city = ArabicCity(
                        arabic_name=city_data[0],
                        iata_code=city_data[1],
                        country_arabic=city_data[2],
                        country_english=city_data[3],
                        timezone=city_data[4],
                        is_popular=city_data[5],
                        popularity_score=city_data[6],
                        alternative_names=city_data[7],
                        latitude=city_data[8],
                        longitude=city_data[9]
                    )
                    db.session.add(city)
            
            # إضافة مدن إنجليزية جديدة
            new_english_cities = [
                ('beijing', 'PEK', 'الصين', 'China', 'Asia/Shanghai', True, 70, 'beijing capital,peking', 39.9042, 116.4074),
                ('delhi', 'DEL', 'الهند', 'India', 'Asia/Kolkata', True, 65, 'new delhi,national capital', 28.6139, 77.2090),
                ('hangzhou', 'HGH', 'الصين', 'China', 'Asia/Shanghai', False, 50, 'hangchow,linan', 30.2741, 120.1551),
                ('guangzhou', 'CAN', 'الصين', 'China', 'Asia/Shanghai', False, 55, 'canton,kwangchow', 23.1291, 113.2644),
                ('khartoum', 'KRT', 'السودان', 'Sudan', 'Africa/Khartoum', False, 40, 'capital of sudan', 15.5007, 32.5599),
                ('casablanca', 'CMN', 'المغرب', 'Morocco', 'Africa/Casablanca', False, 45, 'dar al bayda,casa', 33.5731, -7.5898),
                ('detroit', 'DTW', 'الولايات المتحدة', 'United States', 'America/Detroit', False, 35, 'motor city,det', 42.3314, -83.0458)
            ]
            
            for city_data in new_english_cities:
                if not EnglishCity.query.filter_by(english_name=city_data[0]).first():
                    city = EnglishCity(
                        english_name=city_data[0],
                        iata_code=city_data[1],
                        country_arabic=city_data[2],
                        country_english=city_data[3],
                        timezone=city_data[4],
                        is_popular=city_data[5],
                        popularity_score=city_data[6],
                        alternative_names=city_data[7],
                        latitude=city_data[8],
                        longitude=city_data[9]
                    )
                    db.session.add(city)
            
            # إضافة أسماء بديلة للمدن
            city_aliases_data = [
                ('عمان', 'arabic', 'عمّان', 'AMM'),
                ('القاهره', 'arabic', 'القاهرة', 'CAI'),
                ('خانزو', 'arabic', 'هانغزو', 'HGH'),
                ('كانزو', 'arabic', 'غوانزو', 'CAN'),
                ('دبي', 'arabic', 'دبي', 'DXB'),
                ('استنبول', 'arabic', 'اسطنبول', 'IST'),
                ('amman', 'english', 'amman', 'AMM'),
                ('cairo', 'english', 'cairo', 'CAI'),
                ('hangu', 'english', 'hangzhou', 'HGH'),
                ('canton', 'english', 'guangzhou', 'CAN')
            ]
            
            for alias_data in city_aliases_data:
                if not CityAlias.query.filter_by(alias_name=alias_data[0], city_type=alias_data[1]).first():
                    alias = CityAlias(
                        alias_name=alias_data[0],
                        city_type=alias_data[1],
                        official_city_name=alias_data[2],
                        iata_code=alias_data[3]
                    )
                    db.session.add(alias)
            
            # إضافة إعدادات النظام
            system_settings = [
                ('nlp_confidence_threshold', '0.7', 'حد الثقة في معالجة NLP', 'nlp'),
                ('amadeus_timeout', '30', 'مهلة انتظار Amadeus API (بالثواني)', 'api'),
                ('max_flights_to_show', '5', 'الحد الأقصى لعدد الرحلات المعروضة', 'search'),
                ('default_adults_count', '1', 'عدد البالغين الافتراضي', 'search'),
                ('telegram_bot_enabled', 'true', 'تفعيل بوت التلقرام', 'telegram'),
                ('amadeus_enabled', 'true', 'تفعيل Amadeus API', 'api')
            ]
            
            for setting_data in system_settings:
                if not SystemSettings.query.filter_by(key=setting_data[0]).first():
                    setting = SystemSettings(
                        key=setting_data[0],
                        value=setting_data[1],
                        description=setting_data[2],
                        category=setting_data[3]
                    )
                    db.session.add(setting)
            
            db.session.commit()
            print("✅ تم تحديث البيانات الافتراضية بنجاح!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ خطأ في تحديث البيانات الافتراضية: {e}")

def check_database_health(app):
    """فحص صحة قاعدة البيانات"""
    with app.app_context():
        try:
            # التحقق من الجداول الأساسية
            tables = {
                'arabic_cities': ArabicCity,
                'english_cities': EnglishCity,
                'arabic_months': ArabicMonth,
                'airlines': Airline,
                'search_history': SearchHistory,
                'user_query_patterns': UserQueryPattern
            }
            
            health_report = {}
            for table_name, model in tables.items():
                try:
                    count = model.query.count()
                    health_report[table_name] = {
                        'exists': True,
                        'record_count': count,
                        'status': 'healthy' if count > 0 else 'empty'
                    }
                except Exception as e:
                    health_report[table_name] = {
                        'exists': False,
                        'error': str(e),
                        'status': 'missing'
                    }
            
            return health_report
            
        except Exception as e:
            return {'error': f'فشل فحص الصحة: {str(e)}'}

def backup_database(app):
    """إنشاء نسخة احتياطية من قاعدة البيانات"""
    from datetime import datetime
    
    try:
        if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:///'):
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            if os.path.exists(db_path):
                backup_dir = 'backups'
                os.makedirs(backup_dir, exist_ok=True)
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = os.path.join(backup_dir, f'flight_bot_backup_{timestamp}.db')
                
                shutil.copy2(db_path, backup_path)
                print(f"✅ تم إنشاء نسخة احتياطية في: {backup_path}")
                return backup_path
            else:
                print("❌ ملف قاعدة البيانات غير موجود")
                return None
        else:
            print("⚠️ النسخ الاحتياطي يدعم فقط SQLite حالياً")
            return None
    except Exception as e:
        print(f"❌ فشل إنشاء نسخة احتياطية: {e}")
        return None

def run_migration(app):
    """تشغيل عملية الترقية الكاملة"""
    print("🔍 فحص صحة قاعدة البيانات قبل الترقية...")
    health_before = check_database_health(app)
    print("📊 حالة قاعدة البيانات قبل الترقية:", health_before)
    
    print("🔄 إنشاء نسخة احتياطية...")
    backup_path = backup_database(app)
    
    print("🚀 بدء ترقية قاعدة البيانات...")
    upgrade_database(app)
    
    print("🔍 فحص صحة قاعدة البيانات بعد الترقية...")
    health_after = check_database_health(app)
    print("📊 حالة قاعدة البيانات بعد الترقية:", health_after)
    
    print("🎉 اكتملت عملية الترقية!")
    return {
        'backup_path': backup_path,
        'health_before': health_before,
        'health_after': health_after
    }

if __name__ == '__main__':
    # اختبار الترقية
    test_app = Flask(__name__)
    test_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flight_bot.db'
    test_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(test_app)
    
    # تشغيل الترقية
    migration_result = run_migration(test_app)
    print("🎊 تم الانتهاء من عملية الترقية بنجاح!")