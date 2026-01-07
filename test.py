# populate_cities.py
import os
import sys
from flask import Flask

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def populate_cities():
    """إضافة بيانات المدن إلى قاعدة البيانات"""
    print("🏙️  إضافة بيانات المدن...")
    
    app = Flask(__name__)
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'instance', 'flight_bot.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    try:
        from models import db, City
        
        db.init_app(app)
        
        with app.app_context():
            # بيانات المدن الأساسية
            cities_data = [
                # المدن العربية
                {'iata_code': 'AMM', 'arabic_name': 'عمّان', 'english_name': 'Amman', 'country_arabic': 'الأردن', 'country_english': 'Jordan'},
                {'iata_code': 'CAI', 'arabic_name': 'القاهرة', 'english_name': 'Cairo', 'country_arabic': 'مصر', 'country_english': 'Egypt'},
                {'iata_code': 'RUH', 'arabic_name': 'الرياض', 'english_name': 'Riyadh', 'country_arabic': 'السعودية', 'country_english': 'Saudi Arabia'},
                {'iata_code': 'JED', 'arabic_name': 'جدة', 'english_name': 'Jeddah', 'country_arabic': 'السعودية', 'country_english': 'Saudi Arabia'},
                {'iata_code': 'DMM', 'arabic_name': 'الدمام', 'english_name': 'Dammam', 'country_arabic': 'السعودية', 'country_english': 'Saudi Arabia'},
                {'iata_code': 'DXB', 'arabic_name': 'دبي', 'english_name': 'Dubai', 'country_arabic': 'الإمارات', 'country_english': 'UAE'},
                {'iata_code': 'AUH', 'arabic_name': 'أبو ظبي', 'english_name': 'Abu Dhabi', 'country_arabic': 'الإمارات', 'country_english': 'UAE'},
                {'iata_code': 'SHJ', 'arabic_name': 'الشارقة', 'english_name': 'Sharjah', 'country_arabic': 'الإمارات', 'country_english': 'UAE'},
                {'iata_code': 'DOH', 'arabic_name': 'الدوحة', 'english_name': 'Doha', 'country_arabic': 'قطر', 'country_english': 'Qatar'},
                {'iata_code': 'BAH', 'arabic_name': 'المنامة', 'english_name': 'Manama', 'country_arabic': 'البحرين', 'country_english': 'Bahrain'},
                {'iata_code': 'KWI', 'arabic_name': 'الكويت', 'english_name': 'Kuwait City', 'country_arabic': 'الكويت', 'country_english': 'Kuwait'},
                {'iata_code': 'MCT', 'arabic_name': 'مسقط', 'english_name': 'Muscat', 'country_arabic': 'عمان', 'country_english': 'Oman'},
                {'iata_code': 'BEY', 'arabic_name': 'بيروت', 'english_name': 'Beirut', 'country_arabic': 'لبنان', 'country_english': 'Lebanon'},
                {'iata_code': 'DAM', 'arabic_name': 'دمشق', 'english_name': 'Damascus', 'country_arabic': 'سوريا', 'country_english': 'Syria'},
                {'iata_code': 'BGW', 'arabic_name': 'بغداد', 'english_name': 'Baghdad', 'country_arabic': 'العراق', 'country_english': 'Iraq'},
                
                # المدن العالمية من API
                {'iata_code': 'CDG', 'arabic_name': 'باريس', 'english_name': 'Paris', 'country_arabic': 'فرنسا', 'country_english': 'France'},
                {'iata_code': 'ICN', 'arabic_name': 'سيؤول', 'english_name': 'Seoul', 'country_arabic': 'كوريا الجنوبية', 'country_english': 'South Korea'},
                {'iata_code': 'FRA', 'arabic_name': 'فرانكفورت', 'english_name': 'Frankfurt', 'country_arabic': 'ألمانيا', 'country_english': 'Germany'},
                {'iata_code': 'LHR', 'arabic_name': 'لندن', 'english_name': 'London', 'country_arabic': 'المملكة المتحدة', 'country_english': 'UK'},
                {'iata_code': 'HEL', 'arabic_name': 'هلسنكي', 'english_name': 'Helsinki', 'country_arabic': 'فنلندا', 'country_english': 'Finland'},
                {'iata_code': 'IST', 'arabic_name': 'إسطنبول', 'english_name': 'Istanbul', 'country_arabic': 'تركيا', 'country_english': 'Turkey'},
                {'iata_code': 'JFK', 'arabic_name': 'نيويورك', 'english_name': 'New York', 'country_arabic': 'الولايات المتحدة', 'country_english': 'USA'},
                {'iata_code': 'LAX', 'arabic_name': 'لوس أنجلوس', 'english_name': 'Los Angeles', 'country_arabic': 'الولايات المتحدة', 'country_english': 'USA'},
            ]
            
            added_count = 0
            for city_data in cities_data:
                if not City.query.filter_by(iata_code=city_data['iata_code']).first():
                    city = City(**city_data)
                    db.session.add(city)
                    added_count += 1
                    print(f"➕ {city_data['iata_code']}: {city_data['arabic_name']}")
            
            db.session.commit()
            print(f"✅ تم إضافة {added_count} مدينة إلى قاعدة البيانات")
            
            # التحقق من الإضافة
            total_cities = City.query.count()
            print(f"📊 إجمالي المدن في قاعدة البيانات: {total_cities}")
            
    except Exception as e:
        print(f"❌ خطأ في إضافة المدن: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    populate_cities()