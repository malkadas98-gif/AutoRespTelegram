# flight_api.py
import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from models import Airline, City, Country

load_dotenv()

# إعدادات API
AMADEUS_CLIENT_ID = os.getenv("AMADEUS_CLIENT_ID")
AMADEUS_CLIENT_SECRET = os.getenv("AMADEUS_CLIENT_SECRET")
AMADEUS_AUTH_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
AMADEUS_FLIGHT_SEARCH_URL = "https://test.api.amadeus.com/v2/shopping/flight-offers"

def get_amadeus_token():
    """الحصول على token من Amadeus"""
    try:
        data = {
            'grant_type': 'client_credentials',
            'client_id': AMADEUS_CLIENT_ID,
            'client_secret': AMADEUS_CLIENT_SECRET
        }
        resp = requests.post(AMADEUS_AUTH_URL, data=data, timeout=10)
        resp.raise_for_status()
        return resp.json()['access_token']
    except Exception as e:
        raise Exception(f"فشل في الحصول على token: {str(e)}")

def get_airline_info(iata_code, db_session=None):
    """الحصول على معلومات شركة الطيران من قاعدة البيانات"""
    try:
        if db_session:
            airline = db_session.query(Airline).filter_by(iata_code=iata_code, is_active=True).first()
            if airline:
                return {
                    'arabic_name': airline.arabic_name,
                    'english_name': airline.english_name,
                    'icao_code': airline.icao_code,
                    'country': airline.country.arabic_name if airline.country else 'غير معروف'
                }
        
        # بيانات افتراضية إذا لم توجد في قاعدة البيانات
        default_airlines = {
            'EK': {'arabic_name': 'الإمارات', 'english_name': 'Emirates', 'icao_code': 'UAE', 'country': 'الإمارات'},
            'QR': {'arabic_name': 'الخطوط الجوية القطرية', 'english_name': 'Qatar Airways', 'icao_code': 'QTR', 'country': 'قطر'},
            'SV': {'arabic_name': 'الخطوط الجوية السعودية', 'english_name': 'Saudia', 'icao_code': 'SVA', 'country': 'السعودية'},
            'EY': {'arabic_name': 'الخطوط الجوية الإتحادية', 'english_name': 'Etihad Airways', 'icao_code': 'ETD', 'country': 'الإمارات'},
            'TK': {'arabic_name': 'الخطوط الجوية التركية', 'english_name': 'Turkish Airlines', 'icao_code': 'THY', 'country': 'تركيا'},
            'LH': {'arabic_name': 'لوفتهانزا', 'english_name': 'Lufthansa', 'icao_code': 'DLH', 'country': 'ألمانيا'},
            'BA': {'arabic_name': 'الخطوط الجوية البريطانية', 'english_name': 'British Airways', 'icao_code': 'BAW', 'country': 'المملكة المتحدة'},
            'AF': {'arabic_name': 'الخطوط الجوية الفرنسية', 'english_name': 'Air France', 'icao_code': 'AFR', 'country': 'فرنسا'},
            'FZ': {'arabic_name': 'طيران الإمارات', 'english_name': 'Flydubai', 'icao_code': 'FDB', 'country': 'الإمارات'},
            'GF': {'arabic_name': 'الخطوط الجوية البحرينية', 'english_name': 'Gulf Air', 'icao_code': 'GFA', 'country': 'البحرين'},
            'WY': {'arabic_name': 'الخطوط الجوية العمانية', 'english_name': 'Oman Air', 'icao_code': 'OMA', 'country': 'عمان'},
            'RJ': {'arabic_name': 'الخطوط الجوية الأردنية', 'english_name': 'Royal Jordanian', 'icao_code': 'RJA', 'country': 'الأردن'},
            'MS': {'arabic_name': 'الخطوط الجوية المصرية', 'english_name': 'EgyptAir', 'icao_code': 'MSR', 'country': 'مصر'},
            'KU': {'arabic_name': 'الخطوط الجوية الكويتية', 'english_name': 'Kuwait Airways', 'icao_code': 'KAC', 'country': 'الكويت'},
            'ME': {'arabic_name': 'الخطوط الجوية اللبنانية', 'english_name': 'Middle East Airlines', 'icao_code': 'MEA', 'country': 'لبنان'},
            'G9': {'arabic_name': 'الخطوط الجوية العربية', 'english_name': 'Air Arabia', 'icao_code': 'ABY', 'country': 'الإمارات'}
        }
        
        return default_airlines.get(iata_code, {
            'arabic_name': 'غير معروف',
            'english_name': 'Unknown',
            'icao_code': 'N/A',
            'country': 'غير معروف'
        })
        
    except Exception as e:
        print(f"❌ خطأ في الحصول على معلومات الشركة: {e}")
        return {
            'arabic_name': 'غير معروف',
            'english_name': 'Unknown',
            'icao_code': 'N/A',
            'country': 'غير معروف'
        }

def search_flights_safe(origin, destination, date, adults=1, db_session=None):
    """البحث عن الرحلات بشكل آمن"""
    try:
        token = get_amadeus_token()
        headers = {'Authorization': f'Bearer {token}'}
        
        # التأكد من أن التاريخ في المستقبل
        today = datetime.now().date()
        flight_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        if flight_date <= today:
            # استخدام تاريخ في المستقبل إذا كان التاريخ في الماضي
            new_date = today + timedelta(days=7)
            date = new_date.strftime('%Y-%m-%d')
        
        params = {
            'originLocationCode': origin,
            'destinationLocationCode': destination,
            'departureDate': date,
            'adults': adults,
            'max': 5
        }
        
        resp = requests.get(AMADEUS_FLIGHT_SEARCH_URL, headers=headers, params=params, timeout=15)
        
        if resp.status_code != 200:
            return None
        
        flights_data = resp.json().get('data', [])
        return flights_data
        
    except Exception as e:
        print(f"❌ خطأ في البحث: {e}")
        return None

def get_city_info(iata_code, db_session):
    """الحصول على معلومات المدينة من قاعدة البيانات"""
    try:
        city = db_session.query(City).filter_by(iata_code=iata_code, is_active=True).first()
        if city:
            return {
                'arabic_name': city.arabic_name,
                'english_name': city.english_name,
                'country_arabic': city.country.arabic_name if city.country else 'غير معروف',
                'country_english': city.country.english_name if city.country else 'Unknown'
            }
        
        # إذا لم توجد المدينة في قاعدة البيانات
        return {
            'arabic_name': iata_code,
            'english_name': iata_code,
            'country_arabic': 'غير معروف',
            'country_english': 'Unknown'
        }
        
    except Exception as e:
        print(f"❌ خطأ في الحصول على معلومات المدينة: {e}")
        return {
            'arabic_name': iata_code,
            'english_name': iata_code,
            'country_arabic': 'غير معروف',
            'country_english': 'Unknown'
        }

def format_flight_results(flights_data, db_session=None):
    """تنسيق نتائج الرحلات لعرضها في الواجهة مع معلومات شركات الطيران والمدن"""
    if not flights_data:
        return {
            'success': False,
            'message': '❌ لا توجد رحلات متاحة لهذا المسار والتاريخ.'
        }
    
    flights = []
    for i, flight in enumerate(flights_data[:5], 1):
        try:
            # معلومات الرحلة
            airline_codes = flight.get('validatingAirlineCodes', ['Unknown'])
            airline_code = airline_codes[0] if airline_codes else 'Unknown'
            
            # الحصول على معلومات شركة الطيران
            airline_info = get_airline_info(airline_code, db_session)
            
            itineraries = flight.get('itineraries', [{}])[0]
            segments = itineraries.get('segments', [{}])
            
            if not segments:
                continue
            
            # معلومات التوقيت
            first_segment = segments[0]
            last_segment = segments[-1]
            
            dep_time = first_segment.get('departure', {}).get('at', '').split('T')[1][:5]
            arr_time = last_segment.get('arrival', {}).get('at', '').split('T')[1][:5]
            
            # المطارات والمدن
            dep_airport = first_segment.get('departure', {}).get('iataCode', '')
            arr_airport = last_segment.get('arrival', {}).get('iataCode', '')
            
            # الحصول على أسماء المدن من قاعدة البيانات
            dep_city_info = get_city_info(dep_airport, db_session)
            arr_city_info = get_city_info(arr_airport, db_session)
            
            # معلومات التوقف
            stops = len(segments) - 1
            is_direct = stops == 0
            
            if stops == 0:
                stops_text = "رحلة مباشرة"
            elif stops == 1:
                stops_text = "توقف واحد"
            else:
                stops_text = f"{stops} توقفات"
            
            # مدة الرحلة
            duration = itineraries.get('duration', 'PT0H0M').replace('PT', '').replace('H', 'س ').replace('M', 'د')
            
            # السعر
            price = flight.get('price', {}).get('total', 'غير معروف')
            currency = flight.get('price', {}).get('currency', 'SAR')
            
            # معلومات الطائرة
            aircraft_code = first_segment.get('aircraft', {}).get('code', '')
            aircraft_info = get_aircraft_info(aircraft_code)
            
            flights.append({
                'number': i,
                'airline_code': airline_code,
                'airline_arabic': airline_info['arabic_name'],
                'airline_english': airline_info['english_name'],
                'airline_country': airline_info['country'],
                'airline_icao': airline_info['icao_code'],
                'departure_airport': dep_airport,
                'arrival_airport': arr_airport,
                'departure_city_arabic': dep_city_info['arabic_name'],
                'arrival_city_arabic': arr_city_info['arabic_name'],
                'departure_city_english': dep_city_info['english_name'],
                'arrival_city_english': arr_city_info['english_name'],
                'departure_time': dep_time,
                'arrival_time': arr_time,
                'duration': duration,
                'stops': stops,
                'is_direct': is_direct,
                'stops_text': stops_text,
                'price': price,
                'currency': currency,
                'aircraft': aircraft_info,
                'segments_count': len(segments),
                'flight_class': get_flight_class(flight),
                'direct': is_direct  # حقل إضافي للتوافق
            })
            
        except Exception as e:
            print(f"❌ خطأ في تنسيق الرحلة {i}: {e}")
            continue
    
    return {
        'success': True,
        'flights': flights,
        'count': len(flights),
        'summary': {
            'total_flights': len(flights),
            'direct_flights': len([f for f in flights if f['stops'] == 0]),
            'airlines_count': len(set([f['airline_code'] for f in flights])),
            'lowest_price': min([float(f['price']) for f in flights if f['price'] != 'غير معروف']) if flights else 0
        }
    }

def get_aircraft_info(aircraft_code):
    """الحصول على معلومات الطائرة"""
    aircraft_types = {
        '32A': 'إيرباص A320',
        '32B': 'إيرباص A321',
        '333': 'إيرباص A330-300',
        '77W': 'بوينغ 777-300',
        '788': 'بوينغ 787-8',
        '789': 'بوينغ 787-9',
        '73H': 'بوينغ 737-800',
        '73J': 'بوينغ 737-900',
        '320': 'إيرباص A320',
        '321': 'إيرباص A321',
        '330': 'إيرباص A330',
        '777': 'بوينغ 777',
        '787': 'بوينغ 787',
        '737': 'بوينغ 737'
    }
    return aircraft_types.get(aircraft_code, 'غير معروف')

def get_flight_class(flight):
    """الحصول على فئة الرحلة"""
    try:
        traveler_pricings = flight.get('travelerPricings', [{}])[0]
        fare_details = traveler_pricings.get('fareDetailsBySegment', [{}])[0]
        cabin = fare_details.get('cabin', 'ECONOMY')
        
        cabin_names = {
            'ECONOMY': 'السياحية',
            'PREMIUM_ECONOMY': 'السياحية المميزة',
            'BUSINESS': 'رجال الأعمال',
            'FIRST': 'الأولى'
        }
        
        return cabin_names.get(cabin, 'السياحية')
    except:
        return 'السياحية'

def get_airlines_statistics(db_session):
    """الحصول على إحصائيات شركات الطيران"""
    try:
        total_airlines = db_session.query(Airline).count()
        active_airlines = db_session.query(Airline).filter_by(is_active=True).count()
        
        # أكثر شركات الطيران استخداماً (يمكن تطوير هذا لاحقاً)
        popular_airlines = db_session.query(Airline).filter_by(is_active=True).limit(5).all()
        
        return {
            'total_airlines': total_airlines,
            'active_airlines': active_airlines,
            'popular_airlines': [
                {
                    'iata_code': airline.iata_code,
                    'arabic_name': airline.arabic_name,
                    'english_name': airline.english_name,
                    'country': airline.country.arabic_name if airline.country else 'غير معروف'
                } for airline in popular_airlines
            ]
        }
    except Exception as e:
        print(f"❌ خطأ في الحصول على إحصائيات الشركات: {e}")
        return {
            'total_airlines': 0,
            'active_airlines': 0,
            'popular_airlines': []
        }

def get_cities_by_country(country_code, db_session):
    """الحصول على المدن حسب الدولة"""
    try:
        cities = db_session.query(City).join(Country).filter(
            Country.country_code == country_code,
            City.is_active == True
        ).all()
        
        return [
            {
                'iata_code': city.iata_code,
                'arabic_name': city.arabic_name,
                'english_name': city.english_name,
                'country_arabic': city.country.arabic_name,
                'country_english': city.country.english_name
            }
            for city in cities
        ]
    except Exception as e:
        print(f"❌ خطأ في الحصول على مدن الدولة {country_code}: {e}")
        return []

def get_popular_routes(db_session):
    """الحصول على المسارات الشائعة"""
    try:
        # هذه مجرد أمثلة، يمكن تطويرها لاستخدام بيانات حقيقية من تاريخ البحث
        popular_cities = db_session.query(City).filter_by(is_active=True).limit(8).all()
        
        routes = []
        for i in range(0, len(popular_cities)-1, 2):
            if i+1 < len(popular_cities):
                routes.append({
                    'origin': {
                        'iata_code': popular_cities[i].iata_code,
                        'arabic_name': popular_cities[i].arabic_name,
                        'english_name': popular_cities[i].english_name
                    },
                    'destination': {
                        'iata_code': popular_cities[i+1].iata_code,
                        'arabic_name': popular_cities[i+1].arabic_name,
                        'english_name': popular_cities[i+1].english_name
                    }
                })
        
        return routes
    except Exception as e:
        print(f"❌ خطأ في الحصول على المسارات الشائعة: {e}")
        return []